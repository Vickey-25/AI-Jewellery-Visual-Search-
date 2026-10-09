import type { ReactNode } from "react";

const tones = {
  match: "bg-surface/90 text-ink backdrop-blur-sm shadow-soft",
  neutral: "bg-beige text-brown",
  gold: "bg-champagne text-gold-deep",
} as const;

interface Props {
  tone?: keyof typeof tones;
  className?: string;
  children: ReactNode;
}

export default function Badge({ tone = "neutral", className = "", children }: Props) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium ${tones[tone]} ${className}`}>
      {children}
    </span>
  );
}
