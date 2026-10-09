import type { Facets, SearchFilters } from "../types";

interface Props {
  facets: Facets;
  value: SearchFilters;
  onChange: (next: SearchFilters) => void;
}

interface SelectProps {
  label: string;
  options: string[];
  value: string | undefined;
  onChange: (v: string | undefined) => void;
}

function Select({ label, options, value, onChange }: SelectProps) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value ?? ""} onChange={(e) => onChange(e.target.value || undefined)}>
        <option value="">Any</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function Filters({ facets, value, onChange }: Props) {
  const active = Object.values(value).some((v) => v !== undefined);
  return (
    <details className="filters">
      <summary>Filters{active ? " (on)" : ""}</summary>
      <div className="filters-grid">
        <Select label="Category" options={facets.categories} value={value.category}
          onChange={(category) => onChange({ ...value, category })} />
        <Select label="Material" options={facets.materials} value={value.material}
          onChange={(material) => onChange({ ...value, material })} />
        <Select label="Purity" options={facets.purities} value={value.purity}
          onChange={(purity) => onChange({ ...value, purity })} />
        <Select label="Occasion" options={facets.occasions} value={value.occasion}
          onChange={(occasion) => onChange({ ...value, occasion })} />
        <label className="field">
          <span>Maximum price (₹)</span>
          <input
            type="number"
            min={0}
            step={1000}
            inputMode="numeric"
            placeholder={facets.max_price ? String(Math.round(facets.max_price)) : "No limit"}
            value={value.maxPrice ?? ""}
            onChange={(e) => {
              const n = e.target.value === "" ? undefined : Number(e.target.value);
              onChange({ ...value, maxPrice: n !== undefined && n >= 0 ? n : undefined });
            }}
          />
        </label>
        {active && (
          <button type="button" className="btn btn-link" onClick={() => onChange({})}>
            Clear filters
          </button>
        )}
      </div>
    </details>
  );
}
