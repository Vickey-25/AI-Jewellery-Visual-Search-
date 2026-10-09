import { useEffect, useState } from "react";
import { getProducts } from "../api/productsApi";
import type { Product } from "../types/product";

let cached: Promise<Product[]> | null = null;

interface Sample {
  status: "loading" | "ready" | "error";
  items: Product[];
}

/** One shared request that feeds the home page imagery from the real catalogue. */
export function useCatalogueSample(): Sample {
  const [state, setState] = useState<Sample>({ status: "loading", items: [] });
  useEffect(() => {
    let alive = true;
    cached ??= getProducts({ limit: 100 })
      .then((r) => r.items)
      .catch((e: unknown) => {
        cached = null;
        throw e;
      });
    cached
      .then((items) => alive && setState({ status: "ready", items }))
      .catch(() => alive && setState({ status: "error", items: [] }));
    return () => {
      alive = false;
    };
  }, []);
  return state;
}
