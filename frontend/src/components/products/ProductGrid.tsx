import type { CardProduct } from "../../types/product";
import ProductCard from "./ProductCard";

interface Props {
  items: CardProduct[];
  /** Four columns on very wide screens (used when there is no sidebar). */
  wide?: boolean;
  busy?: boolean;
  onDelete?: (id: number) => void;
}

export default function ProductGrid({ items, wide = false, busy = false, onDelete }: Props) {
  return (
    <div
      aria-busy={busy}
      className={`grid grid-cols-2 gap-x-4 gap-y-8 transition-opacity duration-300 md:grid-cols-3 md:gap-x-6 ${
        wide ? "xl:grid-cols-4" : ""
      } ${busy ? "opacity-50" : ""}`}
    >
      {items.map((p, i) => (
        <ProductCard key={p.id} product={p} index={i} onDelete={onDelete} />
      ))}
    </div>
  );
}
