import { CloudOff, ImageOff, ImagePlus, SearchX } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import SearchComposer from "../components/search/SearchComposer";
import SearchFilters from "../components/search/SearchFilters";
import SearchLoading from "../components/search/SearchLoading";
import SearchResults from "../components/search/SearchResults";
import { Button, ButtonLink } from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Modal from "../components/ui/Modal";
import { useDebounce } from "../hooks/useDebounce";
import { useObjectUrl } from "../hooks/useObjectUrl";
import { useSearch } from "../hooks/useSearch";
import { useSearchDraft } from "../hooks/useSearchDraft";
import { useUrlFilters } from "../hooks/useUrlFilters";
import type { SortKey } from "../types/search";
import { hasActiveFilters } from "../utils/filters";
import { fromSearchResult, sortProducts } from "../utils/product";

const SORT_OPTIONS: SortKey[] = ["match", "price-asc", "price-desc", "newest"];

export default function SearchResultsPage() {
  const { file, setFile } = useSearchDraft();
  const { params, setParams, filters, setFilters, resetFilters } = useUrlFilters();
  const activeText = params.get("q") ?? "";

  const [draftText, setDraftText] = useState(activeText);
  const [imageWeight, setImageWeight] = useState(0.6);
  const [sort, setSort] = useState<SortKey>("match");
  const [filtersOpen, setFiltersOpen] = useState(false);

  const debouncedFilters = useDebounce(filters, 450);
  const debouncedWeight = useDebounce(imageWeight, 600);
  const debouncedDraft = useDebounce(draftText, 700);
  const previewUrl = useObjectUrl(file);

  const commitText = useCallback(
    (value: string) =>
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          const trimmed = value.trim();
          if (trimmed) next.set("q", trimmed);
          else next.delete("q");
          return next;
        },
        { replace: true },
      ),
    [setParams],
  );

  // Follow the URL when the words change from elsewhere (e.g. the header search).
  useEffect(() => {
    setDraftText((current) => (current.trim() === activeText ? current : activeText));
  }, [activeText]);

  // Words alone are cheap to search, so they run as you type. With an image, the customer presses "Find My Match".
  useEffect(() => {
    if (!file && debouncedDraft === draftText && debouncedDraft.trim() !== activeText) commitText(debouncedDraft);
  }, [file, debouncedDraft, draftText, activeText, commitText]);

  const search = useSearch({ file, text: activeText, filters: debouncedFilters, imageWeight: debouncedWeight });
  const { mode, status, error } = search;

  const items = useMemo(() => sortProducts(search.results.map(fromSearchResult), sort), [search.results, sort]);

  const noun = items.length === 1 ? "piece" : "pieces";
  const basis =
    mode === "image" ? "inspired by your image" : mode === "hybrid" ? "inspired by your image and words" : `matching “${activeText}”`;
  const summary = `${items.length} ${noun} ${basis}`;

  const filterPanel = <SearchFilters value={filters} onChange={setFilters} onReset={resetFilters} />;

  return (
    <div className="container-page py-10 sm:py-14">
      <header className="mb-8">
        <p className="eyebrow">Visual search</p>
        <h1 className="mt-3 text-4xl sm:text-5xl">Your AI Matches</h1>
        <p className="mt-3 max-w-xl text-muted">
          {status === "success" && items.length > 0 ? summary : "Share a photo, a few words, or both, and we'll curate pieces for you."}
        </p>
      </header>

      <SearchComposer
        file={file}
        onFileChange={setFile}
        text={draftText}
        onTextChange={setDraftText}
        onSubmit={() => commitText(draftText)}
        canSubmit={draftText.trim() !== activeText}
        imageWeight={imageWeight}
        onImageWeightChange={setImageWeight}
        busy={status === "loading"}
      />

      {mode === "idle" ? (
        <EmptyState icon={ImagePlus} title="Start with a photo or a few words" description="Upload a piece you love, or describe it, and we'll find visually similar jewellery in the collection." />
      ) : (
        <div className="mt-12 lg:grid lg:grid-cols-[17rem_minmax(0,1fr)] lg:gap-12">
          <aside aria-label="Filters" className="hidden lg:block">
            <div className="sticky top-28 max-h-[calc(100vh-8rem)] overflow-y-auto pr-2">{filterPanel}</div>
          </aside>

          <section aria-label="Search results" className="min-w-0">
            {status === "loading" && items.length === 0 && <SearchLoading previewUrl={previewUrl} hasImage={file !== null} />}

            {status === "error" && error && (
              <EmptyState
                icon={error.kind === "invalid-image" ? ImageOff : CloudOff}
                title={error.kind === "invalid-image" ? "That image didn't work" : "We couldn't complete your search"}
                description={error.message}
              >
                <Button variant="primary" onClick={search.retry}>Try Again</Button>
                <ButtonLink to="/products" variant="outline">Explore Collection</ButtonLink>
              </EmptyState>
            )}

            {status === "success" && items.length === 0 && (
              <EmptyState
                icon={SearchX}
                title={file ? "We couldn't find a match." : "No pieces matched your search."}
                description={file ? "Try uploading a clearer jewellery image." : "Try adjusting your filters or using different words."}
              >
                {hasActiveFilters(filters) && <Button variant="primary" onClick={resetFilters}>Reset filters</Button>}
                <ButtonLink to="/products" variant="outline">Explore Collection</ButtonLink>
              </EmptyState>
            )}

            {items.length > 0 && (
              <SearchResults
                items={items}
                summary={summary}
                sort={sort}
                onSortChange={setSort}
                sortOptions={SORT_OPTIONS}
                onOpenFilters={() => setFiltersOpen(true)}
                refreshing={status === "loading"}
              />
            )}
          </section>
        </div>
      )}

      <Modal open={filtersOpen} onClose={() => setFiltersOpen(false)} label="Filters" placement="bottom">
        <div className="p-6">
          {filterPanel}
          <Button variant="primary" size="lg" className="mt-8 w-full" onClick={() => setFiltersOpen(false)}>
            Show results
          </Button>
        </div>
      </Modal>
    </div>
  );
}
