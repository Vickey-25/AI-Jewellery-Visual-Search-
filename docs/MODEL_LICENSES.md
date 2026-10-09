# Model and dependency licences

> **Read this before a commercial launch.** This table was written from the maintainers'
> published licence information as I know it, **without being able to re-check the live pages
> from the build environment**. Licences and model cards change. Confirm every row against the
> current `LICENSE` file / model card, record the exact versions you ship, and get legal advice
> for your jurisdiction. Nothing here is legal advice.

## AI model

| Field | Value |
|---|---|
| Model name | CLIP ViT-B/32 (OpenCLIP identifier `ViT-B-32`) |
| Pretrained weights tag | `laion2b_s34b_b79k` (trained by LAION on LAION-2B-en) |
| Model source | OpenCLIP (`mlfoundations/open_clip`); weights are fetched on first run from the Hugging Face repository `laion/CLIP-ViT-B-32-laion2B-s34B-b79K` |
| Version | Record the exact `open_clip_torch` version (`pip show open_clip_torch`) and the weights tag above |
| Licence | Weights: MIT, as stated on the Hugging Face model card. OpenCLIP code: MIT |
| Commercial-use status | The licence text permits commercial use. See notes |

**Notes**

- The licence of the *weights* is separate from the licence of the *training data*. LAION-2B is a
  large web-scraped dataset (image links + captions) that has not been curated for rights
  clearance. Whether that matters for your business is a legal question; ask counsel.
- The model card for the weights lists limitations and recommends against uncontrolled
  deployment for some uses. A product-similarity search over your own catalogue is a narrow,
  low-risk use, but you should still read the card.
- Do not assume other pretrained tags share this licence. Examples to check individually before
  switching: OpenAI's original CLIP weights (`openai` tag; the code/weights repo is MIT-licensed,
  but OpenAI's model card scopes deployed commercial use as out of scope for research reasons),
  and any `datacomp`, `dfn`, `metaclip` or other tag.
- Changing `MODEL_NAME` / `MODEL_PRETRAINED` changes the embedding space: you must re-run
  `scripts/create_index.py`.

## Libraries and tools

| Component | Licence (as I understand it) | Notes |
|---|---|---|
| PyTorch / torchvision | BSD-3-Clause | CPU wheels used |
| OpenCLIP (`open_clip_torch`) | MIT | |
| FAISS (`faiss-cpu`) | MIT | |
| FastAPI, Pydantic, SQLAlchemy, Alembic | MIT | |
| Uvicorn, NumPy, python-dotenv | BSD-3-Clause | |
| python-multipart | Apache-2.0 | |
| Pillow | HPND (MIT-CMU style) | |
| psycopg 3 (`psycopg[binary]`) | LGPL-3.0 | Used unmodified as a dynamically imported library. LGPL obligations are lighter than GPL, but review them if you redistribute the backend as a packaged binary |
| PostgreSQL | PostgreSQL Licence (permissive) | |
| React, React DOM, Vite, TypeScript | MIT / Apache-2.0 | |
| Jost typeface (Google Fonts) | SIL Open Font Licence 1.1 | Loaded from Google's CDN; self-host it if you do not want browsers contacting Google |

## Demo data

The 24 demo product images are drawn procedurally by `backend/scripts/generate_demo_images.py`.
They are original placeholder illustrations, not photographs, and contain no third-party
material. Product names and prices in the demo catalogue are fictional.
Use your own, rights-cleared photographs for a real catalogue.
