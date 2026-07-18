# Reproducibility checklist

Headline results should not be presented as independently reproducible until a
release satisfies every applicable item below.

## Dataset and evaluation

- [ ] ESCI source URL and immutable version or commit.
- [ ] SHA-256 checksums for every input file.
- [ ] Locale, explicit task, official split, and task-specific membership flag.
- [ ] Every filtering, normalization, join, and deduplication rule.
- [ ] Candidate-corpus construction and qrels generation.
- [ ] Exact relevance gains, tie handling, and metric implementation version.

## Training

- [ ] Git commit SHA and immutable configuration files.
- [ ] Python version and dependency lock.
- [ ] Model identifiers and immutable downloaded-artifact revisions.
- [ ] Hardware, runtime, seeds, batch sizes, and effective sample counts.
- [ ] Raw logs and checkpoint files or checkpoint SHA-256 hashes.

## Reporting

- [ ] At least three independent seeds for learned systems.
- [ ] Per-seed metrics plus clearly defined aggregates and intervals.
- [ ] Raw predictions or run files sufficient to recompute every table.
- [ ] Latency protocol including hardware, warm-up, batch size, and percentiles.
- [ ] A command that regenerates each published table from the raw artifacts.
- [ ] Limitations and failed or contradictory runs retained in the record.

## Bundle layout

```text
results/<release>/
|-- manifest.json
|-- environment.txt
|-- dataset_checksums.txt
|-- configs/
|-- logs/
|-- predictions/
|-- runs/
`-- tables/
```

The required manifest fields are defined by
[`results/manifest.schema.json`](../results/manifest.schema.json). A schema-valid
manifest proves only that metadata is present; it does not prove that the
experiment is scientifically valid.

Until this checklist is complete, public descriptions must not present a
learned benchmark number. Link to the exact repository commit and describe the
result as an unverified experiment or, where provenance is missing, withdraw it.
