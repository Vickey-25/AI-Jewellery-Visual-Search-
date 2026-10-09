import { Heart } from "lucide-react";
import type { MouseEvent } from "react";
import { useFavorites } from "../../hooks/useFavorites";

interface Props {
  productId: number;
  productName: string;
  variant?: "icon" | "full";
  className?: string;
}

export default function WishlistButton({ productId, productName, variant = "icon", className = "" }: Props) {
  const { has, toggle } = useFavorites();
  const active = has(productId);

  const onClick = (e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    toggle(productId);
  };
  const heart = (
    <Heart
      className={`h-[18px] w-[18px] transition-colors ${active ? "animate-heart-pop fill-gold text-gold" : "text-ink"}`}
      strokeWidth={1.7}
      aria-hidden="true"
    />
  );

  if (variant === "full") {
    return (
      <button
        type="button"
        onClick={onClick}
        aria-pressed={active}
        className={`inline-flex h-12 items-center justify-center gap-2 rounded-lg border border-ink/20 px-6 text-sm font-medium transition hover:border-gold ${className}`}
      >
        {heart}
        {active ? "In Your Wishlist" : "Add to Wishlist"}
      </button>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      aria-label={active ? `Remove ${productName} from wishlist` : `Add ${productName} to wishlist`}
      className={`flex h-10 w-10 items-center justify-center rounded-full bg-surface/90 shadow-soft backdrop-blur-sm transition hover:scale-105 ${className}`}
    >
      {heart}
    </button>
  );
}
