import { useEffect, useRef } from "react";
import type { ReactNode } from "react";
import { createPortal } from "react-dom";

type Placement = "center" | "bottom" | "right" | "top";

interface Props {
  open: boolean;
  onClose: () => void;
  label: string;
  placement?: Placement;
  className?: string;
  children: ReactNode;
}

const layout: Record<Placement, { wrap: string; panel: string }> = {
  center: { wrap: "items-center justify-center p-4", panel: "max-w-lg rounded-2xl animate-scale-in" },
  top: { wrap: "items-start justify-center p-4 pt-[10vh]", panel: "max-w-2xl rounded-2xl animate-fade-down" },
  bottom: { wrap: "items-end justify-center", panel: "max-h-[85vh] rounded-t-2xl animate-sheet-up" },
  right: { wrap: "items-stretch justify-end", panel: "max-w-sm rounded-none animate-slide-left" },
};

const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';

/** Accessible dialog: Esc to close, focus is trapped and restored, page scroll is locked. */
export default function Modal({ open, onClose, label, placement = "center", className = "", children }: Props) {
  const panelRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  useEffect(() => {
    closeRef.current = onClose;
  });

  useEffect(() => {
    if (!open) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const panel = panelRef.current;
    const focusables = () => Array.from(panel?.querySelectorAll<HTMLElement>(FOCUSABLE) ?? []);
    (focusables()[0] ?? panel)?.focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        closeRef.current();
        return;
      }
      if (e.key !== "Tab") return;
      const items = focusables();
      if (items.length === 0) {
        e.preventDefault();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
      previouslyFocused?.focus?.();
    };
  }, [open]);

  if (!open) return null;
  const { wrap, panel } = layout[placement];

  return createPortal(
    <div className={`fixed inset-0 z-50 flex animate-fade-in bg-dark/50 backdrop-blur-[2px] ${wrap}`} onMouseDown={onClose}>
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={label}
        tabIndex={-1}
        onMouseDown={(e) => e.stopPropagation()}
        className={`w-full overflow-y-auto bg-ivory shadow-lift outline-none ${panel} ${className}`}
      >
        {children}
      </div>
    </div>,
    document.body,
  );
}
