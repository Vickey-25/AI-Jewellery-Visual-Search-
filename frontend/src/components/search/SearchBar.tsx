import { Search, X } from "lucide-react";
import type { FormEvent } from "react";
import { MAX_QUERY_LENGTH } from "../../config";

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: (value: string) => void;
  placeholder?: string;
  label?: string;
  size?: "md" | "lg";
  className?: string;
}

export default function SearchBar({
  value,
  onChange,
  onSubmit,
  placeholder = "Search jewellery...",
  label = "Search jewellery",
  size = "md",
  className = "",
}: Props) {
  const handle = (e: FormEvent) => {
    e.preventDefault();
    onSubmit?.(value.trim());
  };
  return (
    <form
      role="search"
      onSubmit={handle}
      className={`group flex items-center gap-3 rounded-xl border border-line bg-surface px-4 shadow-soft transition focus-within:border-gold ${
        size === "lg" ? "h-14" : "h-12"
      } ${className}`}
    >
      <Search className="h-5 w-5 flex-none text-muted" strokeWidth={1.6} aria-hidden="true" />
      <input
        type="search"
        value={value}
        maxLength={MAX_QUERY_LENGTH}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label={label}
        className="min-w-0 flex-1 bg-transparent text-ink outline-none placeholder:text-muted/80 [&::-webkit-search-cancel-button]:hidden"
      />
      {value && (
        <button type="button" onClick={() => onChange("")} aria-label="Clear search" className="rounded p-1 text-muted hover:text-ink">
          <X className="h-4 w-4" />
        </button>
      )}
      {onSubmit && (
        <button
          type="submit"
          className="rounded-lg bg-dark px-4 py-1.5 text-sm font-medium text-ivory transition hover:bg-ink disabled:opacity-40"
          disabled={!value.trim()}
        >
          Search
        </button>
      )}
    </form>
  );
}
