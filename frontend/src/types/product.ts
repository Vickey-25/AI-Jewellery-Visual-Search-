/** Mirrors the backend ProductOut schema. */
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
  created_at: string | null;
  updated_at: string | null;
}

export interface ProductListResponse {
  items: Product[];
  page: number;
  limit: number;
  total: number;
}

export interface Facets {
  categories: string[];
  materials: string[];
  purities: string[];
  occasions: string[];
  min_price: number | null;
  max_price: number | null;
}

/** The common shape every product card renders, whether it came from search or the catalogue. */
export interface CardProduct {
  id: number;
  product_code: string;
  name: string;
  category: string;
  material: string;
  purity: string | null;
  weight?: number | null;
  price: number;
  image_url: string | null;
  createdAt?: string | null;
  /** 0..1 retrieval score; only present on search results. */
  matchScore?: number;
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
