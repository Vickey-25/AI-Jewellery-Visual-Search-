import type {
  ApiError,
  Facets,
  Product,
  ProductListResponse,
  ProductQuery,
  SearchFilters,
  SearchResponse,
  EnquiryRequest,
  EnquiryResponse,
} from "../types";

const API_URL = ((import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000").replace(
  /\/+$/,
  "",
);

export class ApiRequestError extends Error {
  code: string;
  status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

/** Turn a backend image path such as "/images/ring_001.jpg" into a full URL. */
export function imageUrl(path: string | null | undefined): string {
  return path ? `${API_URL}${path}` : "";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiRequestError(
      "BACKEND_UNAVAILABLE",
      "Cannot reach the search server. Make sure the backend is running.",
      0,
    );
  }
  if (!response.ok) {
    let code = "UNKNOWN_ERROR";
    let message = "Something went wrong. Please try again.";
    try {
      const body = (await response.json()) as Partial<ApiError>;
      if (body.error) {
        code = body.error.code;
        message = body.error.message;
      }
    } catch {
      // keep the generic message
    }
    throw new ApiRequestError(code, message, response.status);
  }
  return (await response.json()) as T;
}

export function searchByImage(file: File, filters: SearchFilters = {}, topK = 6): Promise<SearchResponse> {
  const form = new FormData(); // multipart upload; no base64
  form.append("image", file);
  form.append("top_k", String(topK));
  if (filters.category) form.append("category", filters.category);
  if (filters.material) form.append("material", filters.material);
  if (filters.purity) form.append("purity", filters.purity);
  if (filters.occasion) form.append("occasion", filters.occasion);
  if (filters.maxPrice !== undefined) form.append("max_price", String(filters.maxPrice));
  return request<SearchResponse>("/api/v1/search/image", { method: "POST", body: form });
}

export function getProducts(query: ProductQuery = {}): Promise<ProductListResponse> {
  const params = new URLSearchParams();
  if (query.page) params.set("page", String(query.page));
  if (query.limit) params.set("limit", String(query.limit));
  if (query.category) params.set("category", query.category);
  if (query.material) params.set("material", query.material);
  if (query.minPrice !== undefined) params.set("min_price", String(query.minPrice));
  if (query.maxPrice !== undefined) params.set("max_price", String(query.maxPrice));
  const qs = params.toString();
  return request<ProductListResponse>(`/api/v1/products${qs ? `?${qs}` : ""}`);
}

export function getProduct(id: number): Promise<Product> {
  return request<Product>(`/api/v1/products/${id}`);
}

export function getSimilarProducts(id: number, topK = 4): Promise<SearchResponse> {
  return request<SearchResponse>(`/api/v1/products/${id}/similar?top_k=${topK}`);
}

export function getFacets(): Promise<Facets> {
  return request<Facets>("/api/v1/products/facets");
}

export function enquireProduct(id: number, data: EnquiryRequest): Promise<EnquiryResponse> {
  return request<EnquiryResponse>(`/api/v1/products/${id}/enquire`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}
