export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
export const ENQUIRY_EMAIL = import.meta.env.VITE_ENQUIRY_EMAIL ?? "concierge@lumiere.example";

/** Matches the backend's upload limit (MAX_IMAGE_SIZE_MB=5). */
export const MAX_UPLOAD_MB = 5;
export const MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024;
export const MAX_QUERY_LENGTH = 200;
/** Backend maximum for top_k. */
export const SEARCH_TOP_K = 20;
