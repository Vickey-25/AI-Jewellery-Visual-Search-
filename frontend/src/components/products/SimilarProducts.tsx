import { useEffect, useState } from "react";
import { isAbortError } from "../../api/client";
import { getSimilarProducts } from "../../api/productsApi";
import { fromSearchResult } from "../../utils/product";
import type { CardProduct } from "../../types/product";
import { ProductGridSkeleton } from "../ui/Skeleton";
import ProductGrid from "./ProductGrid";

export default function SimilarProducts({ productId }: { productId: number }) {
  const [items, setItems] = useState<CardProduct[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setItems(null);
    setFailed(false);
    getSimilarProducts(productId, 4, controller.signal)
      .then((r) => setItems(r.results.map(fromSearchResult)))
      .catch((e: unknown) => {
        if (!isAbortError(e)) setFailed(true);
      });
    return () => controller.abort();
  }, [productId]);

  if (failed || (items && items.length === 0)) return null; // nothing useful to show: stay quiet

  return (
    <section aria-labelledby="similar-heading" className="mt-24">
      <p className="eyebrow">Curated for you</p>
      <h2 id="similar-heading" className="section-title mt-3">AI Similar Pieces</h2>
      <p className="mt-3 max-w-xl text-muted">Pieces with a similar look and feel to this design.</p>
      <div className="mt-10">
        {items === null ? <ProductGridSkeleton count={4} /> : <ProductGrid items={items} wide />}
      </div>
    </section>
  );
}
