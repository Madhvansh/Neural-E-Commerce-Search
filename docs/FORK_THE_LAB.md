# Put neural search on your own catalogue

The browser lab has no project backend, API key, database, or training step. A
fork can become a small semantic-search demo for your own catalogue in about
five minutes.

1. [Fork the repository](https://github.com/Madhvansh/Neural-E-Commerce-Search/fork).
2. Replace the 20 sample products in `docs/catalog.json` with your own public,
   non-sensitive catalogue data. Keep the same five fields. The exact contract
   is published as [`docs/catalog.schema.json`](catalog.schema.json), and the
   lab now reports a readable error instead of silently accepting malformed data.
3. In the fork, enable GitHub Pages with **Deploy from a branch**, branch
   `main`, folder `/docs`.
4. Open `/lab.html` on your Pages site and try a query.

```json
[
  {
    "id": "your-product-id",
    "title": "Product name",
    "category": "Category",
    "description": "A concise searchable description.",
    "tags": ["useful", "search", "terms"]
  }
]
```

The visitor's browser downloads the pinned public MiniLM model and embeds the
catalogue locally. Large catalogues need a different delivery/indexing design;
this remix path is intended for small demonstrations and prototypes.

If you publish a remix, open a
[demo-feedback issue](https://github.com/Madhvansh/Neural-E-Commerce-Search/issues/new?template=demo_feedback.yml)
with the link. Independent remixes are useful evidence and help shape a more
general catalogue adapter.

## Remix Gallery

The first ten independent remixes to share a working link get listed here, each
with a name, a link, and one line on the catalogue. No pull request is required.

To add yours, comment on the remix issue with your published Pages URL (or the
repository) and a one-line description of what it searches:
[Publish one small catalogue remix of the browser lab (issue #6)](https://github.com/Madhvansh/Neural-E-Commerce-Search/issues/6).

| # | Remix | What it searches |
| --- | --- | --- |
| 1–10 | _open — comment on [issue #6](https://github.com/Madhvansh/Neural-E-Commerce-Search/issues/6) to claim a slot_ | — |
