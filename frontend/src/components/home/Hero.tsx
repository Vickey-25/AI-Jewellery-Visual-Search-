import { Link } from "react-router-dom";
import { useCatalogueSample } from "../../hooks/useCatalogueSample";
import { formatCurrency } from "../../utils/formatCurrency";
import ProductImage from "../products/ProductImage";
import { buttonClasses } from "../ui/buttonStyles";
import { ButtonLink } from "../ui/Button";
import Skeleton from "../ui/Skeleton";
import GemArt from "./GemArt";

const POSITIONS = [
  "left-0 top-[4%] w-[44%] -rotate-3",
  "right-0 top-[20%] w-[48%] rotate-2",
  "left-[12%] bottom-0 w-[42%] rotate-1",
];

export default function Hero() {
  const sample = useCatalogueSample();
  // One piece from each of up to three different categories, taken from the live catalogue.
  const picks = sample.items
    .filter((p, i, all) => p.image_url && all.findIndex((q) => q.category === p.category) === i)
    .slice(0, 3);

  return (
    <section className="relative overflow-hidden">
      <div className="container-page grid items-center gap-12 py-14 lg:grid-cols-[1.05fr_0.95fr] lg:gap-8 lg:py-24">
        <div className="animate-fade-up">
          <p className="eyebrow">AI-powered jewellery discovery</p>
          <h1 className="mt-6 text-5xl leading-[1.04] sm:text-6xl lg:text-7xl">
            Find Jewellery
            <br />
            <span className="italic text-gold-deep">That Feels Like You.</span>
          </h1>
          <p className="mt-7 max-w-lg text-lg leading-relaxed text-muted">
            Discover pieces inspired by your style. Upload a jewellery image and let AI find visually similar designs from our collection.
          </p>
          <div className="mt-10 flex flex-col gap-3 sm:flex-row">
            <a href="#visual-search" className={buttonClasses("primary", "lg")}>Find My Jewellery</a>
            <ButtonLink to="/products" variant="outline" size="lg">Explore Collection</ButtonLink>
          </div>
        </div>

        <div className="relative mx-auto aspect-[4/5] w-full max-w-md lg:max-w-none" aria-label="Pieces from the collection">
          <GemArt className="absolute inset-0 h-full w-full animate-float" />
          {sample.status === "loading" &&
            POSITIONS.map((pos) => <Skeleton key={pos} className={`absolute aspect-[4/5] ${pos}`} />)}
          {picks.map((p, i) => (
            <Link
              key={p.id}
              to={`/products/${p.id}`}
              style={{ animationDelay: `${300 + i * 150}ms` }}
              className={`absolute animate-fade-up rounded-xl border border-line bg-surface p-2 shadow-lift transition-transform duration-300 hover:z-10 hover:scale-105 ${POSITIONS[i]}`}
            >
              <div className="aspect-square overflow-hidden rounded-lg bg-beige">
                <ProductImage src={p.image_url} alt={p.name} size={320} priority />
              </div>
              <p className="mt-2 truncate px-1 text-xs font-medium">{p.name}</p>
              <p className="px-1 pb-0.5 text-xs text-muted">{formatCurrency(p.price)}</p>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
