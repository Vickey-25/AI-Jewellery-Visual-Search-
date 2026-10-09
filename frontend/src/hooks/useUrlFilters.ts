import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import type { SearchFilters } from "../types/search";
import { filtersFromParams, filtersToParams } from "../utils/filters";

/** Filters live in the URL so they survive refresh and can be linked to. */
export function useUrlFilters() {
  const [params, setParams] = useSearchParams();
  const key = params.toString();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const filters = useMemo(() => filtersFromParams(params), [key]);

  const setFilters = useCallback(
    (next: SearchFilters) => setParams((prev) => filtersToParams(next, prev), { replace: true }),
    [setParams],
  );
  const resetFilters = useCallback(() => setFilters({}), [setFilters]);

  return { params, setParams, filters, setFilters, resetFilters };
}
