# AI Jewellery Visual Search

Upload a photo of a piece of jewellery and find visually similar products in your catalogue.
Everything runs **locally on CPU**: no paid AI APIs, no GPU, no Docker.

```
Upload image -> Pillow validation -> OpenCLIP embedding -> FAISS search
             -> product IDs -> PostgreSQL -> ranked results in React
```

The API is mobile-ready: a future React Native app can call the same endpoints.

## Contents

1. [Features](#features) · 2. [Architecture](#architecture) · 3. [Technology stack](#technology-stack)
4. [Requirements](#hardware-and-software-requirements) · 5. [Setup (Windows PowerShell)](#setup-windows-powershell)
6. [Run it](#run-it) · 7. [API](#api-documentation) · 8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting) · 10. [Performance](#performance) · 11. [Model licences](#model-licences)
12. [Known limitations](#known-limitations) · 13. [Future improvements](#future-improvements)

## Features

- Image search: `POST /api/v1/search/image` (multipart upload, optional filters, `top_k` 1-20)
- Text search and hybrid (image + text + filters) search with configurable weights
- Product list, product details, and "similar products" endpoints
- Filters: category, material, purity, occasion, price range
- React + TypeScript web app: drag and drop, preview, loading state, product details, similar items
- Uploaded search photos are validated, processed **in memory** and discarded; they are never saved
- Consistent JSON errors, upload size/format limits, restricted CORS, no secrets in code

## Architecture

```
React (Vite) --HTTP/REST--> FastAPI --+--> PostgreSQL  (product data, SQLAlchemy + Alembic)
                                      +--> OpenCLIP    (image/text -> 512-d vector, CPU)
                                      +--> FAISS CPU   (IndexFlatIP over normalised vectors)
```

- `FAISS position -> PostgreSQL product ID` is stored in `backend/data/index/id_mapping.json`.
- Product images live on disk in `backend/data/images/`; only filenames are in PostgreSQL.
- The model is loaded once at startup. FAISS reloads automatically if `create_index.py` rewrites the index.
- The "similarity" shown is a cosine **retrieval score**, not a probability.

```
backend/app/{main.py, config.py, errors.py}
  api/ (search.py, products.py)      thin routes
  services/ (search_service.py, product_service.py)   business logic
  ai/ (clip_service.py, faiss_index.py)
  database/ (database.py, models.py)  schemas/  utils/image_utils.py
backend/{alembic, scripts, tests, data}   web/src/{components, pages, services}
docs/MODEL_LICENSES.md    evaluation/
```

## Technology stack

Python 3.11, FastAPI, Uvicorn, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL, psycopg 3, Pillow, NumPy,
PyTorch (CPU), OpenCLIP, FAISS-CPU, React 18, Vite, TypeScript, plain CSS.

## Hardware and software requirements

Developed for: Windows 11, Intel Core i5-8250U (4 cores / 8 threads), 16 GB RAM, **no NVIDIA GPU**.
Nothing here needs CUDA. Disk: roughly 3 GB for Python packages (PyTorch is large) plus the model weights.

Install first: **Python 3.11**, **PostgreSQL 14+**, **Node.js 18+ (LTS)**. No WSL, no Docker.
Internet is needed once to install packages and to download the model weights (a few hundred MB, cached afterwards).

## Setup (Windows PowerShell)

### 1. Python and virtual environment

```powershell
python --version        # expect 3.11.x   (if not: py -3.11 --version)
cd backend
python -m venv .venv    # or: py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

You never need to "activate" the venv; always call `.\.venv\Scripts\python.exe` directly. This avoids
PowerShell execution-policy problems. On Windows the default PyPI `torch` wheel is CPU-only.

### 2. PostgreSQL

1. Install PostgreSQL from postgresql.org and keep port `5432`. Remember the `postgres` password you set.
2. Make sure the service is running (Services app -> `postgresql-x64-NN` -> Running).
3. Create the database (pgAdmin, or psql):

```sql
CREATE DATABASE jewellery_ai;
```

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE DATABASE jewellery_ai;"
```

### 3. Configure `.env`

```powershell
Copy-Item .env.example .env
notepad .env
```

Set your real password in `DATABASE_URL`:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/jewellery_ai
```

If your password contains characters like `@ : / %`, URL-encode them (`@` becomes `%40`). `.env` is git-ignored; never commit it.

### 4. Migrate, add demo data, build the index

```powershell
.\.venv\Scripts\alembic.exe upgrade head                          # creates the products table
.\.venv\Scripts\python.exe scripts\generate_demo_images.py       # 24 original placeholder images
.\.venv\Scripts\python.exe scripts\seed_products.py              # safe to re-run
.\.venv\Scripts\python.exe scripts\create_index.py               # downloads OpenCLIP weights on first run
```

Expected `create_index.py` output:

```
Connecting to PostgreSQL...
Loading OpenCLIP...
Device: cpu
Products found: 24
Processing:
1/24 ... 24/24
FAISS index created successfully.
Products indexed: 24
```

**Using your own catalogue:** put photos in `backend/data/images/`, insert rows into `products` with matching
`image_filename` values, then re-run `create_index.py`. The demo images are drawings, so similarity on them only
shows that the pipeline works; real photos are needed for meaningful results.

### 5. Frontend

```powershell
cd ..\web
Copy-Item .env.example .env
npm install
```

## Run it

Terminal 1 (PostgreSQL must be running):

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. The startup log shows `Database`, `AI Device`, `OpenCLIP` and `FAISS` status.

Terminal 2:

```powershell
cd web
npm run dev
```

Open http://localhost:5173, drop in a jewellery image, press **Search Similar Jewellery**.

## API documentation

Interactive docs: `/docs`. All responses are JSON. Errors always look like:

```json
{ "success": false, "error": { "code": "INVALID_IMAGE", "message": "Please upload a valid jewellery image." } }
```

| Method & path | Purpose |
|---|---|
| `GET /api/v1/health` | `{status, database, ai_model, faiss_index, device}` (`status` is `degraded` if any part is down) |
| `POST /api/v1/search/image` | multipart: `image` + optional `top_k` (default 5, max 20), `category`, `material`, `purity`, `occasion`, `min_price`, `max_price` |
| `POST /api/v1/search/text` | JSON `{"text": "traditional gold necklace", "top_k": 5, ...filters}` |
| `POST /api/v1/search/hybrid` | multipart: optional `image`, `text`, `image_weight`, `text_weight`, filters (need image or text) |
| `GET /api/v1/products` | `page`, `limit` (max 100), `category`, `material`, `purity`, `occasion`, `min_price`, `max_price` |
| `GET /api/v1/products/{id}` | one product |
| `GET /api/v1/products/{id}/similar` | visually similar products (excludes itself), `top_k` |
| `GET /api/v1/products/facets` | distinct filter values and price range (used by the UI) |
| `GET /images/{filename}` | product images |

Error codes: `INVALID_IMAGE` (400), `UNSUPPORTED_FORMAT` (415), `IMAGE_TOO_LARGE` (413), `VALIDATION_ERROR` (422),
`PRODUCT_NOT_FOUND` / `PRODUCT_NOT_INDEXED` (404), `FAISS_UNAVAILABLE` / `AI_UNAVAILABLE` / `DATABASE_UNAVAILABLE` (503),
`INTERNAL_ERROR` (500). Stack traces go to the server log only.

Notes on scores: image-to-image similarity is typically high (0.7-1.0). Text-to-image CLIP scores are naturally
lower (roughly 0.2-0.35), so for text search read the *ranking*, not the number. Hybrid search rescales each
modality to 0-1 across the catalogue before applying the weights (`HYBRID_IMAGE_WEIGHT`, `HYBRID_TEXT_WEIGHT`
in `.env`, or per request), so its score is a relative ranking score.

Filters: FAISS cannot filter, so with filters active the whole (small) catalogue is ranked and PostgreSQL removes
non-matching rows. That is fine for 20-1,000 products; see future scaling below.

## Testing

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -v
```

- Image validation, error format, missing-index and database-down tests need nothing but the Python packages.
- Product, search and similar-product tests are **skipped automatically** unless PostgreSQL is reachable and the
  index exists. The end-to-end test searches with a catalogue image and checks that the same product comes back first.

Recommended manual order when debugging: PostgreSQL -> DB connection -> Alembic -> seed -> OpenCLIP loads ->
FAISS index -> `/health` -> product API -> `/docs` image search -> React -> upload -> end to end.

Search *quality* is separate from tests: put labelled queries in `evaluation/` and run
`.\.venv\Scripts\python.exe scripts\evaluate.py` to get Recall@5 and Recall@10 (see `evaluation/README.md`).
Make no accuracy claims until you have done this on real data.

## Troubleshooting

**PostgreSQL connection error / `database: false` in `/health`.** Check the service is running, port 5432 is
listening, the database `jewellery_ai` exists, the username and password are right, and `DATABASE_URL` in
`backend/.env` is correct (URL-encode special characters in the password).

**Package installation error.** Run `python --version` and `pip --version`; you need Python 3.11 (64-bit).
Always install with `.\.venv\Scripts\python.exe -m pip ...` so packages go into the venv. Upgrade pip first.

**PowerShell won't activate the venv.** Don't activate it. Use `.\.venv\Scripts\python.exe` and
`.\.venv\Scripts\alembic.exe` directly.

**FAISS error.** Confirm `faiss-cpu` is installed in the venv (`pip show faiss-cpu`), that Python is 3.11, and that
NumPy is a version your faiss-cpu build supports (`pip install -U faiss-cpu numpy`).

**Model download fails on first run.** OpenCLIP downloads weights from Hugging Face once; check your internet,
proxy or firewall. Afterwards it works offline from the cache.

**Search is slow.** CPU inference is slower than GPU; that is expected. The first search after startup can be slower
while PyTorch warms up. Optionally set `TORCH_NUM_THREADS` in `.env` (try 4) and close other heavy apps.

**No results / empty results.** Check `/api/v1/health` -> `faiss_index` is `true`; products exist
(`GET /api/v1/products`); each product's image exists in `backend/data/images/`; `create_index.py` finished without
"SKIPPED" lines; and your filters are not excluding everything.

**Browser shows "Cannot reach the search server".** The backend isn't running, `VITE_API_URL` in `web/.env` is wrong
(restart `npm run dev` after editing), or the web origin isn't in `CORS_ORIGINS`.

## Performance

Choices made for an i5-8250U / 16 GB / CPU-only machine: the small ViT-B/32 model loaded once; 224x224 model input
(images are first shrunk to at most 512 px on the longest side); one inference at a time via a lock; `IndexFlatIP`
(exact search, trivially fast for hundreds to a few thousand vectors); indexed PostgreSQL columns; 5 MB upload cap.
I have not benchmarked on your hardware, so measure the real latency on your machine rather than trusting any number here.

## Model licences

See [`docs/MODEL_LICENSES.md`](docs/MODEL_LICENSES.md). The default weights (`laion2b_s34b_b79k`) are published under MIT,
but check the current model card and your own legal position before commercial use. Do not assume other pretrained
tags share that licence.

## Known limitations

- Search quality on real jewellery is **unmeasured** until you run the evaluation on your own labelled data.
- The bundled demo images are drawings; use real photos for a realistic test.
- CLIP matches overall look and semantics. It does not understand weight, purity or hallmarks.
- No authentication or admin UI: the catalogue is managed through the database and scripts.
- FAISS is in-process, so run a single API worker (`uvicorn` without `--workers`) or each worker loads its own copy.
- Re-run `create_index.py` after adding or changing products or images (the API picks up the new index without a restart).
- The frontend was type-checked against stubs only; run `npm run build` to confirm on your machine.

## Future improvements

Documented, **not** implemented:

- FAISS -> pgvector or Qdrant (filtering inside the vector search, incremental updates, many workers)
- Local image storage -> object storage (S3-compatible) with a CDN
- CPU -> a GPU inference server when traffic grows
- OpenCLIP -> OpenCLIP + DINOv2 fusion for finer visual detail
- React web -> React Native app (camera and gallery) calling `POST /api/v1/search/image`; no separate mobile backend
- Admin: login, product CRUD, image upload, automatic embedding and reindex, inventory, search analytics
- AI: attribute detection, recommendations, chat assistant, virtual try-on
