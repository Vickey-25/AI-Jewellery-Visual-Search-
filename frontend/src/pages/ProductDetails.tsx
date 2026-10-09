import { ArrowLeft, CloudOff, SearchX } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, isAbortError, toApiError } from "../api/client";
import { getProduct } from "../api/productsApi";
import ProductDetails from "../components/products/ProductDetails";
import SimilarProducts from "../components/products/SimilarProducts";
import { Button, ButtonLink } from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Skeleton from "../components/ui/Skeleton";
import type { Product } from "../types/product";

export default function ProductDetailsPage() {
  const { id } = useParams();
  const productId = Number(id);
  const valid = Number.isInteger(productId) && productId > 0;

  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!valid) return;
    const controller = new AbortController();
    setProduct(null);
    setError(null);
    getProduct(productId, controller.signal)
      .then(setProduct)
      .catch((e: unknown) => {
        if (!isAbortError(e)) setError(toApiError(e));
      });
    return () => controller.abort();
  }, [productId, valid, attempt]);

  if (!valid || error?.kind === "not-found") {
    return (
      <EmptyState icon={SearchX} title="We couldn't find that piece" description="It may have been removed from the collection.">
        <ButtonLink to="/products" variant="primary">Explore Collection</ButtonLink>
      </EmptyState>
    );
  }
  if (error) {
    return (
      <EmptyState icon={CloudOff} title="We couldn't load this piece" description={error.message}>
        <Button variant="primary" onClick={() => setAttempt((n) => n + 1)}>Try Again</Button>
        <ButtonLink to="/products" variant="outline">Explore Collection</ButtonLink>
      </EmptyState>
    );
  }

  return (
    <div className="container-page py-10 sm:py-14">
      <nav aria-label="Breadcrumb" className="mb-8 text-sm text-muted">
        <Link to="/products" className="inline-flex items-center gap-2 hover:text-gold-deep">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Back to the collection
        </Link>
      </nav>
      {product ? (
        <>
          <ProductDetails product={product} />
          <SimilarProducts productId={product.id} />
        </>
      ) : (
        <div className="grid gap-10 lg:grid-cols-2 lg:gap-16" role="status" aria-label="Loading piece">
          <Skeleton className="aspect-square w-full rounded-2xl" />
          <div className="space-y-4">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-12 w-3/4" />
            <Skeleton className="h-8 w-32" />
            <Skeleton className="mt-8 h-48 w-full" />
          </div>
        </div>
      )}
    </div>
  );
}
