# Result bundles

This directory is the evidence layer for public benchmark claims. It currently
contains no completed result bundle. Earlier headline figures have been
withdrawn pending a corrected task-specific rerun.

Each published release should add a directory such as `results/v0.2.0/` with:

```text
results/v0.2.0/
|-- manifest.json
|-- environment.txt
|-- dataset_checksums.txt
|-- configs/
|-- logs/
|-- predictions/
|-- runs/
`-- tables/
```

The manifest must identify:

- the exact Git commit and project version;
- the dataset source revision, locale, split, and SHA-256 checksums;
- model identifiers and immutable model revisions;
- Python and dependency versions;
- hardware, runtime, and evaluation protocol;
- every seed and the files that contain its raw outputs;
- the script and command that generated each published table.

Do not commit credentials, private datasets, restricted model artifacts, or
personal data. Large permitted artifacts may be stored in a versioned release or
an archival repository, but their checksums and durable URLs belong in the
manifest.

`manifest.schema.json` defines the minimum machine-readable structure. It does
not validate scientific correctness; review must still compare the declared
protocol with the code and raw files.
