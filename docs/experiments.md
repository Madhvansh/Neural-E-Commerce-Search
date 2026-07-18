# Experiments and evidence status

## Current status

The repository does not currently publish a learned-system benchmark. Earlier
NDCG, recall, and micro-F1 values were withdrawn after a repository audit found
that the available code and artifacts could not establish the reported
protocol. The values must not be copied into papers, posts, repository metadata,
or application material.

The repair separates two official Amazon ESCI populations:

- Task 1 ranking filters the official small_version membership flag.
- Task 2 multiclass classification filters the official large_version flag.

The ranking evaluator now requires the bi-encoder to select candidates before
reranking, computes ideal DCG from the complete qrels, and assigns zero to
missing queries. Hard-negative mining and the second training pass now load the
explicit warmed checkpoint instead of silently restarting from the base model.

These repairs improve evaluation integrity; they do not create new benchmark
evidence. A result becomes publishable only through the bundle below.

## Minimum rerun plan

### 1. Freeze the inputs

- Record the exact Amazon ESCI source commit or immutable dataset revision.
- Publish SHA-256 checksums for every source file.
- Record locale, official task, membership flag, split, candidate construction,
  deduplication, and qrels generation.

### 2. Establish Task 1 ranking baselines

- Run BM25 from a clean checkout.
- Run the dense retriever and retrieve-then-rerank pipeline separately.
- Store complete ranked run files, configs, environment, commands, and logs.
- Use Recall@10 or Recall@20 for the reduced candidate protocol; do not publish
  the previously uninformative Recall@100 value.

### 3. Establish Task 2 classification

- Train and evaluate on the separately filtered large_version population.
- Store raw class predictions and the complete confusion matrix.
- Never imply the Task 1 and Task 2 metrics share one evaluation population.

### 4. Run learned systems repeatedly

- Use at least three independent seeds per learned configuration.
- Record immutable model revisions, hardware, wall-clock runtime, and packages.
- Publish raw predictions, per-seed metrics, logs, and checkpoint hashes.

### 5. Invite independent reproduction

- Test instructions in a fresh environment.
- Open a scoped reproduction issue with expected files and commands.
- Credit reproductions whether they match or contradict the first run.

See [reproducibility.md](reproducibility.md) and
[the result-bundle contract](../results/README.md).
