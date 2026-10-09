export type ButtonVariant = "primary" | "gold" | "outline" | "ghost";
export type ButtonSize = "sm" | "md" | "lg";

const base =
  "inline-flex items-center justify-center gap-2 rounded-lg font-medium tracking-wide transition-all duration-300 " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 focus-visible:ring-offset-ivory " +
  "disabled:pointer-events-none disabled:opacity-50";

const variants: Record<ButtonVariant, string> = {
  primary: "bg-dark text-ivory hover:bg-ink hover:shadow-lift",
  gold: "bg-gold text-dark hover:bg-[#d4b36e] hover:shadow-lift",
  outline: "border border-ink/20 bg-transparent text-ink hover:border-gold hover:text-gold-deep",
  ghost: "text-ink hover:bg-beige",
};

const sizes: Record<ButtonSize, string> = {
  sm: "h-9 px-4 text-sm",
  md: "h-11 px-6 text-sm",
  lg: "h-12 px-8 text-base",
};

export const buttonClasses = (variant: ButtonVariant = "primary", size: ButtonSize = "md", extra = ""): string =>
  `${base} ${variants[variant]} ${sizes[size]} ${extra}`.trim();
