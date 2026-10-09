import { SlidersHorizontal } from "lucide-react";
import type { CardProduct } from "../../types/product";
import type { SortKey } from "../../types/search";
import ProductGrid from "../products/ProductGrid";
import { Button } from "../ui/Button";
import SortSelect from "./SortSelect";

interface Props {
  items: CardProduct[];
  summary: string;
  sort: SortKey;
  onSortChange: (sort: SortKey) => void;
  sortOptions: SortKey[];
  onOpenFilters?: () => void;
  refreshing?: boolean;
  wide?: boolean;
  onDelete?: (id: number) => void;
}

/** Results toolbar (count, filter button on mobile, sort) plus the product grid. */
export default function SearchResults({ items, summary, sort, onSortChange, sortOptions, onOpenFilters, refreshing, wide, onDelete }: Props) {
  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <p className="text-muted" aria-live="polite">{summary}</p>
        <div className="flex items-center gap-3">
          {onOpenFilters && (
            <Button variant="outline" size="sm" onClick={onOpenFilters} className="lg:hidden">
              <SlidersHorizontal className="h-4 w-4" aria-hidden="true" /> Filters
            </Button>
          )}
          <SortSelect value={sort} onChange={onSortChange} options={sortOptions} />
        </div>
      </div>
      <ProductGrid items={items} busy={refreshing} wide={wide} onDelete={onDelete} />
    </div>
  );
}
