import type { EnquiryRequest, EnquiryResponse, Facets, Product, ProductListResponse } from "../types/product";
import type { SearchFilters, SearchResponse } from "../types/search";
import { request } from "./client";

interface ListOptions {
  page?: number;
  limit?: number;
  filters?: SearchFilters;
  signal?: AbortSignal;
}

/** GET /api/v1/products (backend caps `limit` at 100) */
export function getProducts({ page = 1, limit = 20, filters = {}, signal }: ListOptions = {}) {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) });
  if (filters.category) params.set("category", filters.category);
  if (filters.material) params.set("material", filters.material);
  if (filters.purity) params.set("purity", filters.purity);
  if (filters.occasion) params.set("occasion", filters.occasion);
  if (filters.minPrice !== undefined) params.set("min_price", String(filters.minPrice));
  if (filters.maxPrice !== undefined) params.set("max_price", String(filters.maxPrice));
  return request<ProductListResponse>(`/api/v1/products?${params.toString()}`, { signal });
}

/** GET /api/v1/products/{id} */
export function getProduct(id: number, signal?: AbortSignal) {
  return request<Product>(`/api/v1/products/${id}`, { signal });
}

/** GET /api/v1/products/{id}/similar */
export function getSimilarProducts(id: number, topK = 4, signal?: AbortSignal) {
  return request<SearchResponse>(`/api/v1/products/${id}/similar?top_k=${topK}`, { signal });
}

/** GET /api/v1/products/facets: the filter values that really exist in the catalogue */
export function getFacets(signal?: AbortSignal) {
  return request<Facets>("/api/v1/products/facets", { signal });
}

/** POST /api/v1/products/{id}/enquire */
export function enquireProduct(id: number, data: EnquiryRequest, signal?: AbortSignal) {
  return request<EnquiryResponse>(`/api/v1/products/${id}/enquire`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
    signal,
  });
}

/** POST /api/v1/products (Shop Owner only) */
export function createProduct(formData: FormData, signal?: AbortSignal) {
  return request<Product>("/api/v1/products", {
    method: "POST",
    body: formData,
    signal,
  });
}

/** DELETE /api/v1/products/{id} (Shop Owner only) */
export function deleteProduct(id: number, signal?: AbortSignal) {
  return request<{ success: boolean; message: string }>(`/api/v1/products/${id}`, {
    method: "DELETE",
    signal,
  });
}

