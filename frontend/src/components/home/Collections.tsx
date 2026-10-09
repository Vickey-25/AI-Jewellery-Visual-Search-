import { Crown, Flower2, Gem, Sparkles, Sun } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";
import { useCatalogueSample } from "../../hooks/useCatalogueSample";
import ProductImage from "../products/ProductImage";

// Display labels mapped to the category names stored in the catalogue.
const CATEGORIES = [
  { label: "Rings", value: "Ring" },
  { label: "Necklaces", value: "Necklace" },
  { label: "Earrings", value: "Earrings" },
  { label: "Bracelets", value: "Bracelet" },
  { label: "Bangles", value: "Bangle" },
  { label: "Pendants", value: "Pendant" },
];

const OCCASIONS: { value: string; blurb: string; icon: LucideIcon }[] = [
  { value: "Wedding", blurb: "For the day that matters most", icon: Flower2 },
  { value: "Engagement", blurb: "The beginning of forever", icon: Gem },
  { value: "Traditional", blurb: "Heirloom craft, timeless form", icon: Crown },
  { value: "Party", blurb: "Made to catch the light", icon: Sparkles },
  { value: "Daily Wear", blurb: "Quiet luxury for every day", icon: Sun },
];

export default function Collections() {
  const sample = useCatalogueSample();

  return (
    <section id="collections" className="container-page scroll-mt-20 py-20 sm:py-28">
      <div className="max-w-xl">
        <p className="eyebrow">Collections</p>
        <h2 className="section-title mt-3">Shop by Category</h2>
      </div>
      <div className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {CATEGORIES.map((c) => {
          const piece = sample.items.find((p) => p.category === c.value && p.image_url);
          return (
            <Link
              key={c.value}
              to={`/products?category=${encodeURIComponent(c.value)}`}
              className="group relative block aspect-[4/5] overflow-hidden rounded-xl border border-line bg-beige shadow-soft transition duration-300 hover:-translate-y-1 hover:shadow-lift"
            >
              {piece ? (
                <ProductImage src={piece.image_url} alt="" className="transition-transform duration-500 group-hover:scale-[1.05]" />
              ) : (
                <span className="flex h-full items-center justify-center text-gold">
                  <Gem className="h-8 w-8" strokeWidth={1.2} aria-hidden="true" />
                </span>
              )}
              <span className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-dark/70 to-transparent p-4 pt-10 font-display text-lg text-ivory">
                {c.label}
              </span>
            </Link>
          );
        })}
      </div>

      <div className="mt-20 max-w-xl">
        <h2 className="section-title">Shop by Occasion</h2>
      </div>
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {OCCASIONS.map(({ value, blurb, icon: Icon }) => (
          <Link
            key={value}
            to={`/products?occasion=${encodeURIComponent(value)}`}
            className="group rounded-xl border border-line bg-surface p-6 shadow-soft transition duration-300 hover:-translate-y-1 hover:border-gold hover:shadow-lift"
          >
            <Icon className="h-6 w-6 text-gold-deep" strokeWidth={1.4} aria-hidden="true" />
            <h3 className="mt-5 font-display text-xl">{value}</h3>
            <p className="mt-1 text-sm text-muted">{blurb}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
