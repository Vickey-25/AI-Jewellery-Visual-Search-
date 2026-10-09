import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, isAbortError, toApiError } from "../api/client";
import { searchByImage, searchByText, searchHybrid } from "../api/searchApi";
import type { SearchFilters, SearchResult } from "../types/search";
import { fileKey } from "../utils/image";

export type SearchMode = "idle" | "image" | "text" | "hybrid";

interface Params {
  file: File | null;
  text: string;
  filters: SearchFilters;
  imageWeight: number;
}

interface State {
  status: "idle" | "loading" | "success" | "error";
  results: SearchResult[];
  error: ApiError | null;
}

export function searchMode(file: File | null, text: string): SearchMode {
  const hasText = text.trim().length > 0;
  if (file && hasText) return "hybrid";
  if (file) return "image";
  return hasText ? "text" : "idle";
}

/** Runs the real backend search for whatever the customer has provided; cancels stale requests. */
export function useSearch({ file, text, filters, imageWeight }: Params) {
  const [state, setState] = useState<State>({ status: "idle", results: [], error: null });
  const [attempt, setAttempt] = useState(0);
  const lastQuery = useRef("");
  const filtersKey = JSON.stringify(filters);
  const trimmed = text.trim();

  useEffect(() => {
    const mode = searchMode(file, trimmed);
    if (mode === "idle") {
      lastQuery.current = "";
      setState({ status: "idle", results: [], error: null });
      return;
    }

    // A new image or new words clears the old matches; changing only filters keeps them visible.
    const queryId = `${fileKey(file)}|${trimmed}`;
    const isNewQuery = queryId !== lastQuery.current;
    lastQuery.current = queryId;

    const controller = new AbortController();
    const options = { filters: JSON.parse(filtersKey) as SearchFilters, signal: controller.signal };
    setState((s) => ({ status: "loading", results: isNewQuery ? [] : s.results, error: null }));

    const run =
      mode === "hybrid" && file
        ? searchHybrid(file, trimmed, { ...options, imageWeight })
        : mode === "image" && file
          ? searchByImage(file, options)
          : searchByText(trimmed, options);

    run
      .then((res) => setState({ status: "success", results: res.results, error: null }))
      .catch((e: unknown) => {
        if (isAbortError(e)) return;
        setState({ status: "error", results: [], error: toApiError(e) });
      });

    return () => controller.abort();
  }, [file, trimmed, filtersKey, imageWeight, attempt]);

  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  return { ...state, mode: searchMode(file, trimmed), retry };
}
