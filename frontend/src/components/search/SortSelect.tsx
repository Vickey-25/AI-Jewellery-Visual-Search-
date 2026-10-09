import { ChevronDown } from "lucide-react";
import type { SortKey } from "../../types/search";

const LABELS: Record<SortKey, string> = {
  match: "AI Match",
  featured: "Featured",
  "price-asc": "Price: Low to High",
  "price-desc": "Price: High to Low",
  newest: "Newest",
};

interface Props {
  value: SortKey;
  onChange: (value: SortKey) => void;
  options: SortKey[];
}

export default function SortSelect({ value, onChange, options }: Props) {
  return (
    <label className="relative inline-flex items-center gap-3 text-sm">
      <span className="text-muted">Sort by</span>
      <span className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value as SortKey)}
          className="appearance-none rounded-lg border border-line bg-surface py-2 pl-3 pr-9 font-medium outline-none transition focus:border-gold"
        >
          {options.map((key) => (
            <option key={key} value={key}>
              {LABELS[key]}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" aria-hidden="true" />
      </span>
    </label>
  );
}
