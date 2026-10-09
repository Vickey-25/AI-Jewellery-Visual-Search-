import { API_BASE_URL, MAX_UPLOAD_BYTES, MAX_UPLOAD_MB } from "../config";

/** Turns a backend path such as "/images/ring_001.jpg" into an absolute URL. Single source of truth. */
export function resolveImageUrl(path: string | null | undefined): string {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const ALLOWED_EXTENSIONS = /\.(jpe?g|png|webp)$/i;

/** Returns a friendly message if the file can't be used, otherwise null. */
export function validateImageFile(file: File): string | null {
  const typeOk = ALLOWED_TYPES.includes(file.type) || (file.type === "" && ALLOWED_EXTENSIONS.test(file.name));
  if (!typeOk) return "Please choose a JPG, PNG or WebP image.";
  if (file.size === 0) return "That file looks empty. Please choose another image.";
  if (file.size > MAX_UPLOAD_BYTES) return `That image is larger than ${MAX_UPLOAD_MB} MB. Please choose a smaller one.`;
  return null;
}

export const fileKey = (file: File | null): string => (file ? `${file.name}:${file.size}:${file.lastModified}` : "");
