import type { Enquiry, EnquiryListResponse, EnquiryStatus } from "../types/enquiry";
import { request } from "./client";

export function listOwnerEnquiries(status?: string, search?: string, signal?: AbortSignal) {
  const params = new URLSearchParams();
  if (status && status !== "all") params.set("status", status);
  if (search && search.trim()) params.set("search", search.trim());
  const query = params.toString() ? `?${params.toString()}` : "";
  return request<EnquiryListResponse>(`/api/v1/enquiries${query}`, { signal });
}

export function updateEnquiryStatus(enquiryId: number, status: EnquiryStatus, signal?: AbortSignal) {
  return request<Enquiry>(`/api/v1/enquiries/${enquiryId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
    signal,
  });
}

export function listCustomerEnquiries(signal?: AbortSignal) {
  return request<EnquiryListResponse>("/api/v1/enquiries/my", { signal });
}
