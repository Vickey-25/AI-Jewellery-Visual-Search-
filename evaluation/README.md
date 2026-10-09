# Search quality evaluation

Put your own labelled data here, then run `python scripts/evaluate.py` from `backend/`.

- `queries/` — query photos (jpg/png/webp), e.g. customer-style photos of jewellery
- `expected/expected.json` — which catalogue products a human considers relevant:

  ```json
  { "gold_necklace_query.jpg": ["NK001", "NK003"] }
  ```
- `results/` — each run writes a timestamped JSON file with Recall@5 and Recall@10

Recall@K = relevant products found in the top K ÷ all relevant products, averaged over queries.
Until you have run this on a representative labelled set, make no accuracy claims.
