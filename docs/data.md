# Data — Amazon ESCI Shopping Queries

We use the [Amazon ESCI dataset](https://github.com/amazon-science/esci-data)
(*Shopping Queries Dataset: A Large-Scale ESCI Benchmark for Improving Product
Search*, Reddy et al., 2022).

## The ESCI taxonomy

Each (query, product) pair carries one of four relevance labels:

| Label | Name        | Meaning                                                        | Gain |
|-------|-------------|---------------------------------------------------------------|------|
| **E** | Exact       | Product fully matches the query intent                        | 1.0  |
| **S** | Substitute  | Different but functionally interchangeable product            | 0.1  |
| **C** | Complement  | Used *with* the queried item, not a replacement               | 0.01 |
| **I** | Irrelevant  | Unrelated                                                     | 0.0  |

The graded gains in the last column feed the NDCG computation.

## Scale

* **130K+** unique queries across the `us` / `es` / `jp` locales.
* Task 1 ranking uses rows flagged by the official `small_version` column.
* Task 2 multiclass classification uses rows flagged by `large_version`.
* The project defaults to the **`us`** locale and requires an explicit task
  selection; it does not treat an unfiltered table as Task 2.

## Files

The loader (`necs.data.esci.load_esci`) expects the official examples and
products parquet files in
`data/raw/`:

```
shopping_queries_dataset_examples.parquet   # (query_id, query, product_id, esci_label, split, small_version)
shopping_queries_dataset_products.parquet   # (product_id, title, brand, color, bullet_point, description, locale)
shopping_queries_dataset_sources.csv        # query provenance (unused here)
```

Fetch them with:

```bash
python scripts/download_esci.py --locale us --out data/raw
# or, from the Hugging Face mirror:
python scripts/download_esci.py --from-hf --locale us --out data/raw
```

## Preprocessing

* `normalize_text` — NFKC-normalize, strip HTML, lowercase, collapse whitespace.
* `build_product_text` — concatenate product fields (title-first) into one
  passage, truncated to 1024 chars.
* The official `split` column defines the train/test partition
  (`train_test_split`); we never shuffle across it.

## Label balance

ESCI is heavily skewed toward **Exact**. We address this in two places:

* the reranker uses **class weights** `(E=1.0, S=2.0, C=4.0, I=1.5)`;
* hard-negative mining deliberately surfaces **S / C / I** products the
  retriever ranks highly, which is where the headroom is.
