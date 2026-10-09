/** Mirrors the backend SearchResult schema. `similarity` is a 0..1 score, not a probability. */
export interface SearchResult {
  product_id: number;
  product_code: string;
  name: string;
  category: string;
  material: string;
  purity: string | null;
  weight: number | null;
  price: number;
  image_url: string | null;
  similarity: number;
}

export interface SearchResponse {
  query_type: "image" | "text" | "hybrid" | "similar";
  results: SearchResult[];
  total: number;
}

export interface SearchFilters {
  category?: string;
  material?: string;
  purity?: string;
  occasion?: string;
  minPrice?: number;
  maxPrice?: number;
}

export type SortKey = "match" | "featured" | "price-asc" | "price-desc" | "newest";
