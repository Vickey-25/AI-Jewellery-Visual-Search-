import { useFacets } from "../../hooks/useFacets";
import type { SearchFilters as Filters } from "../../types/search";
import { FALLBACK_FACETS, hasActiveFilters } from "../../utils/filters";
import PriceRange from "../ui/PriceRange";

interface Props {
  value: Filters;
  onChange: (next: Filters) => void;
  onReset: () => void;
}

interface GroupProps {
  title: string;
  options: string[];
  selected: string | undefined;
  onSelect: (value: string | undefined) => void;
}

function OptionGroup({ title, options, selected, onSelect }: GroupProps) {
  return (
    <fieldset className="border-t border-line pt-5">
      <legend className="mb-3 font-display text-lg">{title}</legend>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const active = selected?.toLowerCase() === option.toLowerCase();
          return (
            <button
              key={option}
              type="button"
              aria-pressed={active}
              onClick={() => onSelect(active ? undefined : option)}
              className={`rounded-lg border px-3 py-1.5 text-sm transition ${
                active ? "border-dark bg-dark text-ivory" : "border-line bg-surface hover:border-gold"
              }`}
            >
              {option}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

const roundDown = (n: number) => Math.floor(n / 1000) * 1000;
const roundUp = (n: number) => Math.ceil(n / 1000) * 1000;

/** Options and the price range come from the API, with static defaults if it is unreachable. */
export default function SearchFilters({ value, onChange, onReset }: Props) {
  const facets = useFacets();
  const categories = facets?.categories.length ? facets.categories : FALLBACK_FACETS.categories;
  const materials = facets?.materials.length ? facets.materials : FALLBACK_FACETS.materials;
  const purities = facets?.purities.length ? facets.purities : FALLBACK_FACETS.purities;
  const occasions = facets?.occasions.length ? facets.occasions : FALLBACK_FACETS.occasions;
  const lowest = facets?.min_price != null ? roundDown(facets.min_price) : FALLBACK_FACETS.minPrice;
  const highest = facets?.max_price != null ? Math.max(roundUp(facets.max_price), lowest + 1000) : FALLBACK_FACETS.maxPrice;

  const lo = Math.max(lowest, value.minPrice ?? lowest);
  const hi = Math.min(highest, value.maxPrice ?? highest);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-2xl">Filters</h2>
        {hasActiveFilters(value) && (
          <button type="button" onClick={onReset} className="text-sm font-medium text-gold-deep hover:underline">
            Reset filters
          </button>
        )}
      </div>
      <OptionGroup title="Category" options={categories} selected={value.category} onSelect={(category) => onChange({ ...value, category })} />
      <OptionGroup title="Material" options={materials} selected={value.material} onSelect={(material) => onChange({ ...value, material })} />
      <OptionGroup title="Purity" options={purities} selected={value.purity} onSelect={(purity) => onChange({ ...value, purity })} />
      <OptionGroup title="Occasion" options={occasions} selected={value.occasion} onSelect={(occasion) => onChange({ ...value, occasion })} />
      <fieldset className="border-t border-line pt-5">
        <legend className="mb-4 font-display text-lg">Price</legend>
        <PriceRange
          min={lowest}
          max={highest}
          value={[lo, hi]}
          onChange={([a, b]) =>
            onChange({ ...value, minPrice: a > lowest ? a : undefined, maxPrice: b < highest ? b : undefined })
          }
        />
      </fieldset>
    </div>
  );
}
