"""Train the bi-encoder retriever with in-batch + hard negatives.

Stage 1 of the pipeline. The first pass trains on in-batch negatives only;
after :mod:`necs.data.hard_negatives` mines hard negatives from the warmed-up
retriever, re-running with ``--hard-negatives <path>`` fine-tunes against them.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from necs.config import Config, load_config
from necs.data.datasets import BiEncoderDataset, make_retriever_collate
from necs.data.esci import load_esci, train_test_split
from necs.models.bi_encoder import BiEncoder
from necs.training.losses import info_nce_loss
from necs.utils.logging import get_logger
from necs.utils.seed import seed_everything

logger = get_logger(__name__)


def _build_scheduler(optimizer, num_steps: int, warmup_ratio: float):
    from transformers import get_linear_schedule_with_warmup

    warmup = int(num_steps * warmup_ratio)
    return get_linear_schedule_with_warmup(optimizer, warmup, num_steps)


def train_bi_encoder(
    config: Config,
    hard_negatives: dict[int, list[str]] | None = None,
    init_from: str | None = None,
    output_dir: str | Path | None = None,
) -> BiEncoder:
    seed_everything(config.train.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cfg = config.bi_encoder

    examples = load_esci(config.data.raw_dir, config.data.locale, config.data.task)
    train_ex, _ = train_test_split(examples)

    model_source = init_from or cfg.model_name
    model = BiEncoder(model_source, cfg.pooling, cfg.normalize).to(device)
    dataset = BiEncoderDataset(train_ex, hard_negatives, cfg.num_hard_negatives)
    collate = make_retriever_collate(model.tokenizer, cfg.max_seq_len)
    loader = DataLoader(
        dataset,
        batch_size=cfg.batch_size,
        shuffle=True,
        collate_fn=collate,
        num_workers=config.train.num_workers,
        drop_last=True,
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr)
    total_steps = len(loader) * cfg.epochs
    scheduler = _build_scheduler(optimizer, total_steps, cfg.warmup_ratio)
    scaler = torch.cuda.amp.GradScaler(enabled=config.train.fp16 and device == "cuda")

    model.train()
    for epoch in range(cfg.epochs):
        running = 0.0
        for step, batch in enumerate(loader):
            query = {k: v.to(device) for k, v in batch["query"].items()}
            doc = {k: v.to(device) for k, v in batch["doc"].items()}
            optimizer.zero_grad()
            with torch.cuda.amp.autocast(enabled=scaler.is_enabled()):
                q_emb, d_emb = model(query, doc)
                loss = info_nce_loss(q_emb, d_emb, cfg.temperature)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            running += loss.item()
            if step % 100 == 0:
                logger.info("epoch %d step %d loss %.4f", epoch, step, loss.item())
        logger.info("epoch %d mean loss %.4f", epoch, running / max(len(loader), 1))

    out = Path(output_dir or config.train.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    model.save(str(out))
    (out / "bi_encoder_meta.json").write_text(
        json.dumps(
            {
                "base_model_name": cfg.model_name,
                "initialized_from": init_from,
                "pooling": cfg.pooling,
            },
            indent=2,
        )
    )
    logger.info("Saved retriever to %s", out)
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/bi_encoder.yaml")
    parser.add_argument("--hard-negatives", default=None, help="mined negatives JSON")
    parser.add_argument(
        "--init-from",
        default=None,
        help="checkpoint used to initialize this training pass",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="override the configured checkpoint output directory",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    negatives = None
    if args.hard_negatives:
        raw = json.loads(Path(args.hard_negatives).read_text())
        negatives = {int(k): v for k, v in raw.items()}
        logger.info("Loaded hard negatives for %d queries", len(negatives))
    train_bi_encoder(
        config,
        negatives,
        init_from=args.init_from,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
