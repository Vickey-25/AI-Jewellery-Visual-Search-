import type { SearchFilters } from "../types/search";

export const hasActiveFilters = (f: SearchFilters): boolean =>
  Object.values(f).some((v) => v !== undefined && v !== "");

const num = (v: string | null): number | undefined => {
  if (v === null || v === "") return undefined;
  const n = Number(v);
  return Number.isFinite(n) && n >= 0 ? n : undefined;
};

export function filtersFromParams(p: URLSearchParams): SearchFilters {
  return {
    category: p.get("category") || undefined,
    material: p.get("material") || undefined,
    purity: p.get("purity") || undefined,
    occasion: p.get("occasion") || undefined,
    minPrice: num(p.get("min_price")),
    maxPrice: num(p.get("max_price")),
  };
}

/** Writes filters onto a copy of `base`, leaving unrelated params (like `q`) alone. */
export function filtersToParams(f: SearchFilters, base: URLSearchParams): URLSearchParams {
  const next = new URLSearchParams(base);
  for (const key of ["category", "material", "purity", "occasion", "min_price", "max_price"]) next.delete(key);
  if (f.category) next.set("category", f.category);
  if (f.material) next.set("material", f.material);
  if (f.purity) next.set("purity", f.purity);
  if (f.occasion) next.set("occasion", f.occasion);
  if (f.minPrice !== undefined) next.set("min_price", String(f.minPrice));
  if (f.maxPrice !== undefined) next.set("max_price", String(f.maxPrice));
  return next;
}

/** Used only if the facets endpoint is unreachable. */
export const FALLBACK_FACETS = {
  categories: ["Necklace", "Ring", "Earrings", "Bracelet", "Bangle", "Pendant"],
  materials: ["Gold", "Silver", "Diamond"],
  purities: ["22K", "18K", "925"],
  occasions: ["Wedding", "Engagement", "Traditional", "Party", "Daily Wear"],
  minPrice: 2000,
  maxPrice: 150000,
};
