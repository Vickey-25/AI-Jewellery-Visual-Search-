import { ImagePlus, RefreshCw, Sparkles, X } from "lucide-react";
import { useRef, useState } from "react";
import type { ChangeEvent, DragEvent, KeyboardEvent } from "react";
import { MAX_UPLOAD_MB } from "../../config";
import { useObjectUrl } from "../../hooks/useObjectUrl";
import { validateImageFile } from "../../utils/image";

interface Props {
  file: File | null;
  onChange: (file: File | null) => void;
  variant?: "hero" | "compact";
  disabled?: boolean;
}

export default function ImageUploader({ file, onChange, variant = "hero", disabled = false }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const preview = useObjectUrl(file);

  const accept = (candidate: File | undefined) => {
    if (!candidate) return;
    const problem = validateImageFile(candidate);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    onChange(candidate);
  };
  const browse = () => !disabled && inputRef.current?.click();
  const onPick = (e: ChangeEvent<HTMLInputElement>) => {
    accept(e.target.files?.[0]);
    e.target.value = "";
  };
  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (!disabled) accept(e.dataTransfer.files?.[0]);
  };
  const onZoneKey = (e: KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      browse();
    }
  };
  const remove = () => {
    setError(null);
    onChange(null);
  };

  const input = (
    <input
      ref={inputRef}
      type="file"
      className="sr-only"
      tabIndex={-1}
      accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
      onChange={onPick}
      aria-label="Upload a jewellery image"
    />
  );
  const errorLine = error && (
    <p role="alert" className="mt-3 text-sm text-[#9a3a2e]">
      {error}
    </p>
  );

  if (variant === "compact") {
    return (
      <div>
        {input}
        {file ? (
          <div className="flex items-center gap-4">
            <img src={preview ?? undefined} alt="Your uploaded jewellery" className="h-20 w-20 flex-none rounded-lg border border-line object-cover" />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{file.name}</p>
              <div className="mt-2 flex gap-4 text-sm">
                <button type="button" onClick={browse} disabled={disabled} className="inline-flex items-center gap-1.5 font-medium text-gold-deep hover:underline">
                  <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" /> Replace
                </button>
                <button type="button" onClick={remove} disabled={disabled} className="inline-flex items-center gap-1.5 text-muted hover:text-ink">
                  <X className="h-3.5 w-3.5" aria-hidden="true" /> Remove
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div
            role="button"
            tabIndex={0}
            onClick={browse}
            onKeyDown={onZoneKey}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            className={`flex h-20 cursor-pointer items-center justify-center gap-3 rounded-xl border border-dashed text-sm transition ${
              dragging ? "border-gold bg-champagne" : "border-gold/50 bg-ivory hover:bg-champagne/60"
            }`}
          >
            <ImagePlus className="h-5 w-5 text-gold-deep" strokeWidth={1.5} aria-hidden="true" />
            Add a photo
          </div>
        )}
        {errorLine}
      </div>
    );
  }

  return (
    <div>
      {input}
      {file ? (
        <div className="relative animate-scale-in overflow-hidden rounded-2xl border border-line bg-surface p-3 shadow-soft">
          <div className="flex max-h-[420px] min-h-[240px] items-center justify-center overflow-hidden rounded-xl bg-beige">
            <img src={preview ?? undefined} alt="Your uploaded jewellery" className="max-h-[420px] w-full object-contain" />
          </div>
          <div className="absolute right-6 top-6 flex gap-2">
            <button
              type="button"
              onClick={browse}
              disabled={disabled}
              className="inline-flex items-center gap-1.5 rounded-lg bg-surface/95 px-3 py-1.5 text-sm font-medium shadow-soft backdrop-blur-sm transition hover:text-gold-deep"
            >
              <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" /> Replace
            </button>
            <button
              type="button"
              onClick={remove}
              disabled={disabled}
              aria-label="Remove image"
              className="inline-flex items-center gap-1.5 rounded-lg bg-dark px-3 py-1.5 text-sm font-medium text-ivory shadow-soft transition hover:bg-ink"
            >
              <X className="h-3.5 w-3.5" aria-hidden="true" /> Remove
            </button>
          </div>
        </div>
      ) : (
        <div
          role="button"
          tabIndex={0}
          aria-label="Choose a jewellery image or drop one here"
          onClick={browse}
          onKeyDown={onZoneKey}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={`flex min-h-[300px] cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed px-6 py-12 text-center transition-all duration-300 ${
            dragging ? "scale-[1.01] border-gold bg-champagne" : "border-gold/60 bg-surface hover:bg-champagne/50"
          }`}
        >
          <span className="flex h-16 w-16 items-center justify-center rounded-full border border-gold/50 bg-champagne text-gold-deep">
            <Sparkles className="h-7 w-7" strokeWidth={1.3} aria-hidden="true" />
          </span>
          <p className="mt-6 font-display text-2xl">Drop your jewellery image here</p>
          <p className="mt-2 text-muted">
            or <span className="font-medium text-gold-deep underline underline-offset-4">browse from your device</span>
          </p>
          <p className="mt-6 text-xs tracking-wide text-muted">JPG, PNG or WebP • Up to {MAX_UPLOAD_MB} MB</p>
        </div>
      )}
      {errorLine}
    </div>
  );
}
