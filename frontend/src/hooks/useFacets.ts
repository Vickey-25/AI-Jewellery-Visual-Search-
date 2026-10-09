import { useEffect, useState } from "react";
import { getFacets } from "../api/productsApi";
import type { Facets } from "../types/product";

let cached: Promise<Facets> | null = null;

/** Filter options come from the API (once per session). Null means "not available". */
export function useFacets(): Facets | null {
  const [facets, setFacets] = useState<Facets | null>(null);
  useEffect(() => {
    let alive = true;
    cached ??= getFacets().catch((e: unknown) => {
      cached = null;
      throw e;
    });
    cached.then((f) => alive && setFacets(f)).catch(() => alive && setFacets(null));
    return () => {
      alive = false;
    };
  }, []);
  return facets;
}
