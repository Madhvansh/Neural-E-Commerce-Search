"""Train the DeBERTa cross-encoder reranker on ESCI 4-class labels.

Stage 2 of the pipeline. Trains on labelled (query, product) pairs with a
class-weighted cross-entropy that compensates for the heavy Exact-label skew.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from necs.config import Config, load_config
from necs.data.datasets import (
    CrossEncoderDataset,
    class_distribution,
    make_cross_encoder_collate,
)
from necs.data.esci import load_esci, train_test_split
from necs.models.cross_encoder import CrossEncoder
from necs.training.losses import weighted_cross_entropy
from necs.utils.logging import get_logger
from necs.utils.seed import seed_everything

logger = get_logger(__name__)


def _build_scheduler(optimizer, num_steps: int, warmup_ratio: float):
    from transformers import get_linear_schedule_with_warmup

    return get_linear_schedule_with_warmup(
        optimizer, int(num_steps * warmup_ratio), num_steps
    )


def train_cross_encoder(config: Config) -> CrossEncoder:
    seed_everything(config.train.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cfg = config.cross_encoder

    examples = load_esci(config.data.raw_dir, config.data.locale, config.data.task)
    train_ex, _ = train_test_split(examples)
    logger.info("Label distribution: %s", class_distribution(train_ex))

    model = CrossEncoder(cfg.model_name, cfg.num_labels).to(device)
    dataset = CrossEncoderDataset(train_ex, model.tokenizer, cfg.max_seq_len)
    collate = make_cross_encoder_collate(model.tokenizer)
    loader = DataLoader(
        dataset,
        batch_size=cfg.batch_size,
        shuffle=True,
        collate_fn=collate,
        num_workers=config.train.num_workers,
    )

    weights = torch.tensor(cfg.class_weights, device=device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay
    )
    accum = config.train.grad_accum_steps
    total_steps = (len(loader) // accum) * cfg.epochs
    scheduler = _build_scheduler(optimizer, total_steps, cfg.warmup_ratio)
    scaler = torch.cuda.amp.GradScaler(enabled=config.train.fp16 and device == "cuda")

    model.train()
    for epoch in range(cfg.epochs):
        running = 0.0
        optimizer.zero_grad()
        for step, batch in enumerate(loader):
            labels = batch.pop("labels").to(device)
            batch = {k: v.to(device) for k, v in batch.items()}
            with torch.cuda.amp.autocast(enabled=scaler.is_enabled()):
                logits = model(**batch)
                loss = weighted_cross_entropy(logits, labels, weights) / accum
            scaler.scale(loss).backward()
            if (step + 1) % accum == 0:
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad()
            running += loss.item() * accum
            if step % 100 == 0:
                logger.info("epoch %d step %d loss %.4f", epoch, step, loss.item() * accum)
        logger.info("epoch %d mean loss %.4f", epoch, running / max(len(loader), 1))

    out = Path(config.train.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    model.save(str(out))
    logger.info("Saved reranker to %s", out)
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/cross_encoder.yaml")
    args = parser.parse_args()
    train_cross_encoder(load_config(args.config))


if __name__ == "__main__":
    main()
