import { Heart } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { getProduct } from "../api/productsApi";
import { ApiError } from "../api/client";
import ProductGrid from "../components/products/ProductGrid";
import { ButtonLink } from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import { ProductGridSkeleton } from "../components/ui/Skeleton";
import { useFavorites } from "../hooks/useFavorites";
import type { Product } from "../types/product";
import { fromProduct } from "../utils/product";

export default function Favorites() {
  const { ids, remove } = useFavorites();
  const cache = useRef(new Map<number, Product>());
  const [loading, setLoading] = useState(ids.length > 0);
  const [, setVersion] = useState(0);

  useEffect(() => {
    const missing = ids.filter((id) => !cache.current.has(id));
    if (missing.length === 0) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    Promise.allSettled(missing.map((id) => getProduct(id, controller.signal))).then((results) => {
      if (controller.signal.aborted) return;
      results.forEach((result, i) => {
        if (result.status === "fulfilled") cache.current.set(missing[i], result.value);
        else if (result.reason instanceof ApiError && result.reason.kind === "not-found") remove(missing[i]);
      });
      setVersion((v) => v + 1);
      setLoading(false);
    });
    return () => controller.abort();
  }, [ids, remove]);

  const items = ids.flatMap((id) => {
    const p = cache.current.get(id);
    return p ? [fromProduct(p)] : [];
  });

  return (
    <div className="container-page py-10 sm:py-14">
      <header className="mb-10">
        <p className="eyebrow">Wishlist</p>
        <h1 className="mt-3 text-4xl sm:text-5xl">Your Favorites</h1>
        <p className="mt-3 text-muted">Saved on this device, so they're here when you come back.</p>
      </header>

      {ids.length === 0 ? (
        <EmptyState icon={Heart} title="Nothing saved yet" description="Tap the heart on any piece to keep it here.">
          <ButtonLink to="/products" variant="primary">Explore Collection</ButtonLink>
          <ButtonLink to="/search" variant="outline">Search by image</ButtonLink>
        </EmptyState>
      ) : loading && items.length === 0 ? (
        <ProductGridSkeleton count={Math.min(ids.length, 8)} />
      ) : (
        <ProductGrid items={items} wide />
      )}
    </div>
  );
}
