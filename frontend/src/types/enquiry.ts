import type { Product } from "./product";

export type EnquiryStatus = "pending" | "contacted" | "completed" | "cancelled";

export interface Enquiry {
  id: number;
  product_id: number;
  user_id: number | null;
  name: string;
  email: string;
  phone: string | null;
  status: EnquiryStatus;
  message: string | null;
  created_at: string;
  product: Product | null;
}

export interface EnquiryListResponse {
  items: Enquiry[];
  total: number;
}
