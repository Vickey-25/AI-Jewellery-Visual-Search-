import { Sparkles } from "lucide-react";
import { MAX_QUERY_LENGTH } from "../../config";
import { Button } from "../ui/Button";
import ImageUploader from "./ImageUploader";
import SearchBar from "./SearchBar";

interface Props {
  file: File | null;
  onFileChange: (file: File | null) => void;
  text: string;
  onTextChange: (text: string) => void;
  /** Applies the words together with the image (hybrid search). */
  onSubmit: () => void;
  canSubmit: boolean;
  imageWeight: number;
  onImageWeightChange: (value: number) => void;
  busy?: boolean;
}

/** Image + words in one place: the hybrid search experience. */
export default function SearchComposer({
  file,
  onFileChange,
  text,
  onTextChange,
  onSubmit,
  canSubmit,
  imageWeight,
  onImageWeightChange,
  busy = false,
}: Props) {
  const hybrid = file !== null && text.trim().length > 0;

  return (
    <section aria-label="Refine your search" className="rounded-2xl border border-line bg-surface p-5 shadow-soft sm:p-6">
      <div className="grid gap-6 md:grid-cols-[minmax(0,20rem)_1fr] md:gap-8">
        <ImageUploader file={file} onChange={onFileChange} variant="compact" disabled={busy && file !== null} />

        <div className="flex flex-col justify-center gap-4">
          <SearchBar
            value={text}
            onChange={onTextChange}
            placeholder={file ? "Add words to refine, e.g. gold engagement ring" : "Or describe it, e.g. gold wedding necklace"}
            label="Describe the jewellery you want"
            onSubmit={() => onSubmit()}
          />
          <p className="text-sm text-muted">
            {file
              ? "Combine your photo with a few words for a more personal match."
              : `Up to ${MAX_QUERY_LENGTH} characters. Or add a photo for a visual match.`}
          </p>

          {hybrid && (
            <div className="rounded-xl bg-ivory p-4">
              <label htmlFor="balance" className="flex items-center justify-between text-sm font-medium">
                <span>Balance</span>
                <span className="text-xs font-normal text-muted">{Math.round(imageWeight * 100)}% image / {Math.round((1 - imageWeight) * 100)}% words</span>
              </label>
              <input
                id="balance"
                type="range"
                min={0.1}
                max={0.9}
                step={0.1}
                value={imageWeight}
                onChange={(e) => onImageWeightChange(Number(e.target.value))}
                className="mt-3 w-full accent-[#C9A45C]"
              />
              <div className="mt-1 flex justify-between text-xs text-muted">
                <span>Your words</span>
                <span>Your image</span>
              </div>
            </div>
          )}

          {file && (
            <div>
              <Button variant="primary" size="lg" onClick={onSubmit} disabled={!canSubmit || busy}>
                <Sparkles className="h-4 w-4" aria-hidden="true" />
                Find My Match
              </Button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
