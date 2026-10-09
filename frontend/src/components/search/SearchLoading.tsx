import { Check, Gem } from "lucide-react";
import { useEffect, useState } from "react";

const IMAGE_STEPS = ["Identifying shape", "Understanding style", "Finding visual matches", "Curating your results"];
const TEXT_STEPS = ["Reading your description", "Understanding style", "Finding matches", "Curating your results"];

interface Props {
  previewUrl?: string | null;
  hasImage?: boolean;
}

export default function SearchLoading({ previewUrl, hasImage = true }: Props) {
  const steps = hasImage ? IMAGE_STEPS : TEXT_STEPS;
  const [active, setActive] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setActive((n) => Math.min(n + 1, steps.length - 1)), 1700);
    return () => clearInterval(id);
  }, [steps.length]);

  return (
    <div className="flex animate-fade-in flex-col items-center py-14 text-center" role="status" aria-live="polite">
      <div className="relative flex h-40 w-40 items-center justify-center">
        <span className="absolute inset-0 animate-ring-pulse rounded-full border border-gold/60" />
        <span className="absolute inset-0 animate-ring-pulse rounded-full border border-gold/40 [animation-delay:1.2s]" />
        <span className="relative flex h-28 w-28 items-center justify-center overflow-hidden rounded-full border border-gold bg-champagne shadow-soft">
          {hasImage && previewUrl ? (
            <img src={previewUrl} alt="" className="h-full w-full object-cover opacity-90" />
          ) : (
            <Gem className="h-10 w-10 text-gold-deep" strokeWidth={1.2} aria-hidden="true" />
          )}
        </span>
      </div>

      <h2 className="mt-8 font-display text-2xl sm:text-3xl">{hasImage ? "Analyzing your jewellery..." : "Searching the collection..."}</h2>
      <p className="mt-2 text-muted">AI is discovering your perfect matches...</p>

      <ol className="mt-8 space-y-3 text-left">
        {steps.map((step, i) => {
          const done = i < active;
          const current = i === active;
          return (
            <li
              key={step}
              className={`flex items-center gap-3 text-sm transition-all duration-500 ${
                done || current ? "opacity-100" : "opacity-35"
              } ${current ? "text-ink" : "text-muted"}`}
            >
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full border transition-colors duration-500 ${
                  done ? "border-gold bg-gold text-dark" : current ? "border-gold" : "border-line"
                }`}
              >
                {done ? <Check className="h-3 w-3" strokeWidth={3} aria-hidden="true" /> : current ? <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gold" /> : null}
              </span>
              {step}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
