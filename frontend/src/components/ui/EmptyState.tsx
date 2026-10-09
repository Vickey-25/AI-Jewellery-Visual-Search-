import { Gem } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface Props {
  title: string;
  description?: string;
  icon?: LucideIcon;
  children?: ReactNode;
}

export default function EmptyState({ title, description, icon: Icon = Gem, children }: Props) {
  return (
    <div className="mx-auto flex max-w-md animate-fade-in flex-col items-center px-4 py-16 text-center" role="status">
      <span className="mb-6 flex h-16 w-16 items-center justify-center rounded-full border border-gold/40 bg-champagne text-gold-deep">
        <Icon className="h-7 w-7" strokeWidth={1.4} aria-hidden="true" />
      </span>
      <h2 className="font-display text-2xl leading-snug">{title}</h2>
      {description && <p className="mt-3 text-muted">{description}</p>}
      {children && <div className="mt-8 flex flex-wrap items-center justify-center gap-3">{children}</div>}
    </div>
  );
}
