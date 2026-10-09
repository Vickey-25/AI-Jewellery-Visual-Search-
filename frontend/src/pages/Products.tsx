import { CloudOff, Plus, SearchX } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { deleteProduct } from "../api/productsApi";
import AddProductModal from "../components/products/AddProductModal";
import SearchBar from "../components/search/SearchBar";
import SearchFilters from "../components/search/SearchFilters";
import SearchResults from "../components/search/SearchResults";
import { Button, ButtonLink } from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Modal from "../components/ui/Modal";
import { ProductGridSkeleton } from "../components/ui/Skeleton";
import { useAuth } from "../hooks/useAuth";
import { useDebounce } from "../hooks/useDebounce";
import { useProducts } from "../hooks/useProducts";
import { useUrlFilters } from "../hooks/useUrlFilters";
import type { SortKey } from "../types/search";
import { hasActiveFilters } from "../utils/filters";
import { fromProduct, sortProducts } from "../utils/product";

const SORT_OPTIONS: SortKey[] = ["featured", "price-asc", "price-desc", "newest"];
const PAGE_SIZE = 12;

export default function Products() {
  const navigate = useNavigate();
  const { isOwner } = useAuth();
  const { filters, setFilters, resetFilters } = useUrlFilters();
  const debounced = useDebounce(filters, 350);
  const { status, items, error, retry } = useProducts(debounced);

  const [sort, setSort] = useState<SortKey>("featured");
  const [visible, setVisible] = useState(PAGE_SIZE);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => setVisible(PAGE_SIZE), [debounced]);

  const cards = useMemo(() => sortProducts(items.map(fromProduct), sort), [items, sort]);
  const shown = cards.slice(0, visible);
  const filterPanel = <SearchFilters value={filters} onChange={setFilters} onReset={resetFilters} />;

  const handleDeleteProduct = async (id: number) => {
    try {
      await deleteProduct(id);
      retry();
    } catch (err: any) {
      alert(err?.message || "Failed to remove product.");
    }
  };

  return (
    <div className="container-page py-10 sm:py-14">
      <header className="mb-10 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <p className="eyebrow">Discover</p>
            {isOwner && (
              <span className="rounded-full bg-ink px-2.5 py-0.5 text-[10px] font-semibold text-gold tracking-wider uppercase">
                Owner Access
              </span>
            )}
          </div>
          <h1 className="mt-3 text-4xl sm:text-5xl">The Collection</h1>
          <p className="mt-3 max-w-md text-muted">Browse every piece, or search by photo to find a design you love.</p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full md:max-w-md">
          {isOwner && (
            <button
              type="button"
              onClick={() => setAddModalOpen(true)}
              className="flex items-center justify-center gap-2 rounded-xl bg-ink px-4 py-2.5 text-xs font-semibold text-gold hover:bg-black transition shadow-md shrink-0"
            >
              <Plus className="h-4 w-4 text-gold" />
              <span>+ Add Jewellery</span>
            </button>
          )}

          <SearchBar
            value={query}
            onChange={setQuery}
            onSubmit={(v) => v && navigate(`/search?q=${encodeURIComponent(v)}`)}
            placeholder="Search jewellery..."
            className="flex-1"
          />
        </div>
      </header>

      <div className="lg:grid lg:grid-cols-[17rem_minmax(0,1fr)] lg:gap-12">
        <aside aria-label="Filters" className="hidden lg:block">
          <div className="sticky top-28 max-h-[calc(100vh-8rem)] overflow-y-auto pr-2">{filterPanel}</div>
        </aside>

        <section aria-label="Products" className="min-w-0">
          {status === "loading" && items.length === 0 && <ProductGridSkeleton count={8} />}

          {status === "error" && error && (
            <EmptyState icon={CloudOff} title="We couldn't load the collection" description={error.message}>
              <Button variant="primary" onClick={retry}>Try Again</Button>
            </EmptyState>
          )}

          {status === "success" && cards.length === 0 && (
            <EmptyState icon={SearchX} title="No pieces matched your search." description="Try adjusting your filters or uploading another image.">
              {hasActiveFilters(filters) && <Button variant="primary" onClick={resetFilters}>Reset filters</Button>}
              <ButtonLink to="/search" variant="outline">Search by image</ButtonLink>
            </EmptyState>
          )}

          {cards.length > 0 && (
            <>
              <SearchResults
                items={shown}
                summary={`${cards.length} ${cards.length === 1 ? "piece" : "pieces"}`}
                sort={sort}
                onSortChange={setSort}
                sortOptions={SORT_OPTIONS}
                onOpenFilters={() => setFiltersOpen(true)}
                refreshing={status === "loading"}
                wide
                onDelete={isOwner ? handleDeleteProduct : undefined}
              />
              {visible < cards.length && (
                <div className="mt-12 text-center">
                  <p className="mb-4 text-sm text-muted">Showing {shown.length} of {cards.length}</p>
                  <Button variant="outline" size="lg" onClick={() => setVisible((n) => n + PAGE_SIZE)}>
                    Load more
                  </Button>
                </div>
              )}
            </>
          )}
        </section>
      </div>

      <Modal open={filtersOpen} onClose={() => setFiltersOpen(false)} label="Filters" placement="bottom">
        <div className="p-6">
          {filterPanel}
          <Button variant="primary" size="lg" className="mt-8 w-full" onClick={() => setFiltersOpen(false)}>
            Show results
          </Button>
        </div>
      </Modal>

      <AddProductModal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        onProductAdded={() => {
          retry();
        }}
      />
    </div>
  );
}
