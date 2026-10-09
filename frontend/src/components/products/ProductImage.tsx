import { Gem } from "lucide-react";
import { useState } from "react";
import { resolveImageUrl } from "../../utils/image";

interface Props {
  src: string | null;
  alt: string;
  className?: string;
  /** Intrinsic size hints so the layout doesn't jump while images load. */
  size?: number;
  priority?: boolean;
}

/** Lazy image with an elegant fallback instead of a broken-image icon. */
export default function ProductImage({ src, alt, className = "", size = 512, priority = false }: Props) {
  const [failed, setFailed] = useState(false);
  const url = resolveImageUrl(src);

  if (!url || failed) {
    return (
      <div role="img" aria-label="Jewellery image unavailable" className="flex h-full w-full flex-col items-center justify-center gap-2 bg-beige text-muted">
        <Gem className="h-8 w-8 text-gold" strokeWidth={1.2} aria-hidden="true" />
        <span className="text-xs tracking-wide">Jewellery image unavailable</span>
      </div>
    );
  }
  return (
    <img
      src={url}
      alt={alt}
      width={size}
      height={size}
      loading={priority ? "eager" : "lazy"}
      decoding="async"
      onError={() => setFailed(true)}
      className={`h-full w-full object-cover ${className}`}
    />
  );
}
