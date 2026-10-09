import { SEARCH_TOP_K } from "../config";
import type { SearchFilters, SearchResponse } from "../types/search";
import { request } from "./client";

interface SearchOptions {
  filters?: SearchFilters;
  topK?: number;
  signal?: AbortSignal;
}

function appendFilters(form: FormData, f: SearchFilters = {}): void {
  if (f.category) form.append("category", f.category);
  if (f.material) form.append("material", f.material);
  if (f.purity) form.append("purity", f.purity);
  if (f.occasion) form.append("occasion", f.occasion);
  if (f.minPrice !== undefined) form.append("min_price", String(f.minPrice));
  if (f.maxPrice !== undefined) form.append("max_price", String(f.maxPrice));
}

/** POST /api/v1/search/image (multipart) */
export function searchByImage(file: File, { filters, topK = SEARCH_TOP_K, signal }: SearchOptions = {}) {
  const form = new FormData();
  form.append("image", file);
  form.append("top_k", String(topK));
  appendFilters(form, filters);
  return request<SearchResponse>("/api/v1/search/image", { method: "POST", body: form, signal });
}

/** POST /api/v1/search/text (JSON) */
export function searchByText(text: string, { filters = {}, topK = SEARCH_TOP_K, signal }: SearchOptions = {}) {
  return request<SearchResponse>("/api/v1/search/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      top_k: topK,
      category: filters.category ?? null,
      material: filters.material ?? null,
      purity: filters.purity ?? null,
      occasion: filters.occasion ?? null,
      min_price: filters.minPrice ?? null,
      max_price: filters.maxPrice ?? null,
    }),
    signal,
  });
}

/** POST /api/v1/search/hybrid (multipart). `imageWeight` is 0..1; the text gets the remainder. */
export function searchHybrid(
  file: File,
  text: string,
  { filters, topK = SEARCH_TOP_K, signal, imageWeight = 0.6 }: SearchOptions & { imageWeight?: number } = {},
) {
  const form = new FormData();
  form.append("image", file);
  form.append("text", text);
  form.append("top_k", String(topK));
  form.append("image_weight", String(imageWeight));
  form.append("text_weight", String(Math.max(0, 1 - imageWeight)));
  appendFilters(form, filters);
  return request<SearchResponse>("/api/v1/search/hybrid", { method: "POST", body: form, signal });
}
