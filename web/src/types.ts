export interface Product {
  id: number;
  product_code: string;
  name: string;
  description: string | null;
  category: string;
  material: string;
  purity: string | null;
  weight: number | null;
  price: number;
  stone_type: string | null;
  colour: string | null;
  occasion: string | null;
  image_filename: string | null;
  image_url: string | null;
  is_active: boolean;
}

/** `similarity` is a retrieval score between 0 and 1, not a probability. */
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
  query_type: string;
  results: SearchResult[];
  total: number;
}

export interface ProductListResponse {
  items: Product[];
  page: number;
  limit: number;
  total: number;
}

export interface ApiError {
  success: false;
  error: { code: string; message: string };
}

export interface Facets {
  categories: string[];
  materials: string[];
  purities: string[];
  occasions: string[];
  min_price: number | null;
  max_price: number | null;
}

export interface SearchFilters {
  category?: string;
  material?: string;
  purity?: string;
  occasion?: string;
  maxPrice?: number;
}

export interface ProductQuery {
  page?: number;
  limit?: number;
  category?: string;
  material?: string;
  minPrice?: number;
  maxPrice?: number;
}

export interface EnquiryRequest {
  name: string;
  email: string;
  message?: string;
}

export interface EnquiryResponse {
  success: boolean;
  message: string;
}
