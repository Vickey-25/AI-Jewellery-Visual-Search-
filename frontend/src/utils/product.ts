import type { CardProduct, Product } from "../types/product";
import type { SearchResult, SortKey } from "../types/search";

export const fromSearchResult = (r: SearchResult): CardProduct => ({
  id: r.product_id,
  product_code: r.product_code,
  name: r.name,
  category: r.category,
  material: r.material,
  purity: r.purity,
  weight: r.weight,
  price: r.price,
  image_url: r.image_url,
  matchScore: r.similarity,
});

export const fromProduct = (p: Product): CardProduct => ({
  id: p.id,
  product_code: p.product_code,
  name: p.name,
  category: p.category,
  material: p.material,
  purity: p.purity,
  weight: p.weight,
  price: p.price,
  image_url: p.image_url,
  createdAt: p.created_at,
});

/** Sorting happens in the browser: the backend returns AI-ranked or id-ordered lists. */
export function sortProducts(items: CardProduct[], sort: SortKey): CardProduct[] {
  const copy = [...items];
  switch (sort) {
    case "price-asc":
      return copy.sort((a, b) => a.price - b.price);
    case "price-desc":
      return copy.sort((a, b) => b.price - a.price);
    case "newest":
      // Search results carry no timestamp, so a higher id (added later) counts as newer.
      return copy.sort((a, b) => {
        const byDate = (b.createdAt ?? "").localeCompare(a.createdAt ?? "");
        return byDate !== 0 ? byDate : b.id - a.id;
      });
    default:
      return copy; // "match" and "featured" keep the server order
  }
}
