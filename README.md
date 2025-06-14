# Neural E-Commerce Search

Two-stage retrieve-and-rank neural product search on the Amazon ESCI
Shopping Queries dataset.

> 🚧 Early scaffold — see `docs/` and the roadmap for what is landing.

## Goal

Given a shopping query, return a ranked list of products and classify each
result as **E**xact / **S**ubstitute / **C**omplement / **I**rrelevant
(the ESCI taxonomy). A dense bi-encoder retrieves candidates; a DeBERTa
cross-encoder reranks them.

## Layout

```
src/necs/      library code (data, models, training, retrieval, eval, api)
configs/       experiment configuration
scripts/       data download, training, evaluation entry points
tests/         test suite
docs/          design notes and experiment logs
```

## License

MIT — see [LICENSE](LICENSE).
