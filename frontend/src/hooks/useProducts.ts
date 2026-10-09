import { useCallback, useEffect, useState } from "react";
import { ApiError, isAbortError, toApiError } from "../api/client";
import { getProducts } from "../api/productsApi";
import type { Product } from "../types/product";
import type { SearchFilters } from "../types/search";

interface State {
  status: "loading" | "success" | "error";
  items: Product[];
  error: ApiError | null;
}

/** Catalogue listing. The demo catalogue is small, so one page of up to 100 is fetched and paged in the UI. */
export function useProducts(filters: SearchFilters) {
  const [state, setState] = useState<State>({ status: "loading", items: [], error: null });
  const [attempt, setAttempt] = useState(0);
  const filtersKey = JSON.stringify(filters);

  useEffect(() => {
    const controller = new AbortController();
    setState((s) => ({ ...s, status: "loading", error: null }));
    getProducts({ limit: 100, filters: JSON.parse(filtersKey) as SearchFilters, signal: controller.signal })
      .then((r) => setState({ status: "success", items: r.items, error: null }))
      .catch((e: unknown) => {
        if (isAbortError(e)) return;
        setState({ status: "error", items: [], error: toApiError(e) });
      });
    return () => controller.abort();
  }, [filtersKey, attempt]);

  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  return { ...state, retry };
}
