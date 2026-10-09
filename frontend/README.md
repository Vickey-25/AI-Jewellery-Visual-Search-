# Lumière: AI Jewellery frontend

React 18 + TypeScript + Vite + Tailwind CSS 3 + React Router 6 + Lucide icons. No other runtime dependencies.
It talks only to the existing FastAPI backend; nothing in the UI is mocked or hardcoded.

## Run

```powershell
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run build        # type-check + production build
npm run lint
```

The backend must be running at `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`).
Configuration lives in `.env` (copy from `.env.example`); restart `npm run dev` after editing it.

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Backend base URL. The only place the API location is defined (`src/config.ts`) |
| `VITE_ENQUIRY_EMAIL` | Address used by "Enquire About This Piece" (a `mailto:` link) |

CORS: the backend's `.env` already allows `http://localhost:5173` and `http://127.0.0.1:5173`. If you serve the
frontend from another origin, add it to `CORS_ORIGINS` in the backend `.env`.

## Pages

| Route | What it is |
|---|---|
| `/` | Hero, **See it. Upload it. Find it.** search section, category and occasion collections, story, how it works |
| `/search` | "Your AI Matches": image, text or image + text (hybrid), filters, sorting. Text lives in `?q=`, filters in the URL too |
| `/products` | Catalogue with filters, sorting, text search box and "Load more" |
| `/products/:id` | Product details, wishlist, enquiry, **AI Similar Pieces** |
| `/favorites` | Wishlist (localStorage) |
| `/about` | Story, privacy and customer-care anchors |

## How the three search modes map to the backend

| Customer provides | Request |
|---|---|
| Image only | `POST /api/v1/search/image` (multipart) |
| Words only | `POST /api/v1/search/text` (JSON). Runs as you type (debounced) |
| Image + words | `POST /api/v1/search/hybrid` (multipart, with a balance slider sent as `image_weight` / `text_weight`) |

Filters (category, material, purity, occasion, price) are sent to the backend and applied server-side. Stale
requests are cancelled with `AbortController`. Filter options and the price range come from `GET /api/v1/products/facets`.

## Structure

```
src/
  api/          client.ts (fetch wrapper: timeout, cancel, friendly errors), searchApi.ts, productsApi.ts
  components/   layout/ search/ products/ home/ ui/
  context/      favorites (localStorage) and the picked-image draft
  hooks/        useSearch, useProducts, useFacets, useDebounce, useUrlFilters, ...
  pages/        Home, SearchResults, Products, ProductDetails, Favorites, About, NotFound
  types/ utils/ config.ts
```

## Image strategy

The frontend contains **no product images**. Every product image comes from the `image_url` the API returns
(e.g. `/images/ring_001.jpg`), converted to an absolute URL in one place: `resolveImageUrl()` in `src/utils/image.ts`.
The home page's hero and category tiles use pieces from the live catalogue, and the hero artwork is an inline SVG.
To move to real photos or a CDN, change what the backend serves; no React change is needed.

## Notes and deliberate differences from the brief

- **Upload limit is 5 MB, not 10 MB.** The backend rejects anything larger (`MAX_IMAGE_SIZE_MB=5`), so the UI enforces the same
  limit up front instead of letting the server refuse it. GIFs are not accepted by the backend either.
- **Up to 20 results per search** (the backend's `top_k` maximum). The demo catalogue has 24 products.
- **Sorting is done in the browser.** The backend has no sort parameter. "Newest" uses `created_at` on the catalogue page; search
  results don't include a timestamp, so there a higher product id counts as newer.
- **The "92% visual match" is the backend's similarity score** for image searches. For text and hybrid searches the score has a
  different scale (the backend documents this), so the UI shows the match badge but you should read the *ranking*.
- Fonts (Playfair Display, Inter) load from Google Fonts with Georgia / system-ui fallbacks.
- Footer social links point to the networks' home pages, and the shipping/returns pages are honest placeholders until real policies exist.
