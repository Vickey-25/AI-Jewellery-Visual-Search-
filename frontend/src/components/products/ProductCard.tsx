import { ArrowRight, Sparkles, Trash2 } from "lucide-react";
import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import type { CardProduct } from "../../types/product";
import { formatCurrency } from "../../utils/formatCurrency";
import Badge from "../ui/Badge";
import ProductImage from "./ProductImage";
import WishlistButton from "./WishlistButton";

interface Props {
  product: CardProduct;
  index?: number;
  onDelete?: (id: number) => void;
}

export default function ProductCard({ product, index = 0, onDelete }: Props) {
  const { isOwner } = useAuth();
  const [deleting, setDeleting] = useState(false);

  const match = product.matchScore !== undefined
    ? product.matchScore === 1
      ? "100"
      : (product.matchScore * 100).toFixed(2)
    : null;
  const spec = [product.purity, product.material, product.weight ? `${product.weight}g` : null].filter(Boolean).join(" ");
  const meta = [product.category, spec].filter(Boolean).join(" · ");
  const href = `/products/${product.id}`;

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (window.confirm(`Are you sure you want to remove "${product.name}" (${product.product_code}) from the catalogue?`)) {
      setDeleting(true);
      if (onDelete) {
        onDelete(product.id);
      }
    }
  };

  return (
    <article
      className={`group relative animate-fade-up transition-transform duration-300 hover:-translate-y-1 ${
        deleting ? "opacity-40 pointer-events-none" : ""
      }`}
      style={{ animationDelay: `${Math.min(index, 11) * 60}ms` }}
    >
      <div className="overflow-hidden rounded-xl border border-line bg-surface shadow-soft transition-shadow duration-300 group-hover:shadow-lift">
        <Link to={href} tabIndex={-1} aria-hidden="true" className="block">
          <div className="relative aspect-square overflow-hidden bg-beige">
            <ProductImage
              src={product.image_url}
              alt={product.name}
              className="transition-transform duration-500 ease-out group-hover:scale-[1.03]"
            />
            {match !== null && (
              <Badge tone="match" className="absolute bottom-3 right-3">
                <Sparkles className="h-3 w-3 text-gold" aria-hidden="true" />
                {match}% visual match
              </Badge>
            )}
          </div>
        </Link>
        <Link to={href} className="block p-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-gold">
          <h3 className="font-display text-lg leading-snug">{product.name}</h3>
          <p className="mt-1 text-sm text-muted">{meta}</p>
          <p className="mt-0.5 text-xs tracking-wide text-muted/80">{product.product_code}</p>
          <p className="mt-3 text-lg font-medium">{formatCurrency(product.price)}</p>
          <span className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-gold-deep">
            View Details
            <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" aria-hidden="true" />
          </span>
        </Link>
      </div>

      <WishlistButton productId={product.id} productName={product.name} className="absolute left-3 top-3" />

      {/* Owner Remove/Delete Action */}
      {isOwner && onDelete && (
        <button
          type="button"
          onClick={handleDelete}
          className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-red-600/90 text-white shadow-md transition hover:bg-red-700 hover:scale-105"
          title="Remove jewellery piece (Owner only)"
          aria-label={`Remove ${product.name}`}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      )}
    </article>
  );
}
