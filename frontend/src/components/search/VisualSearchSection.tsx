import { Sparkles } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { MAX_QUERY_LENGTH } from "../../config";
import { useSearchDraft } from "../../hooks/useSearchDraft";
import { Button } from "../ui/Button";
import ImageUploader from "./ImageUploader";
import SearchBar from "./SearchBar";

/** The centrepiece: upload an image (optionally with words) and go to the matches. */
export default function VisualSearchSection() {
  const { file, setFile } = useSearchDraft();
  const [text, setText] = useState("");
  const navigate = useNavigate();

  const go = (value: string) => navigate(value.trim() ? `/search?q=${encodeURIComponent(value.trim())}` : "/search");

  return (
    <section id="visual-search" aria-labelledby="vs-heading" className="scroll-mt-20 border-y border-line bg-surface py-20 sm:py-28">
      <div className="container-page">
        <div className="mx-auto max-w-2xl text-center">
          <p className="eyebrow">Search by image</p>
          <h2 id="vs-heading" className="mt-4 font-display text-4xl leading-tight sm:text-5xl">
            See it. Upload it. Find it.
          </h2>
          <p className="mt-5 text-lg text-muted">
            Upload a photo of jewellery you love and our AI will discover similar pieces from the collection.
          </p>
        </div>

        <div className="mx-auto mt-12 max-w-3xl">
          <ImageUploader file={file} onChange={setFile} />

          {file ? (
            <div className="mt-6 animate-fade-up">
              <p className="mb-3 text-center text-sm text-muted">Optional: add a few words to refine your match</p>
              <input
                type="text"
                value={text}
                maxLength={MAX_QUERY_LENGTH}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && go(text)}
                aria-label="Describe the jewellery you want"
                placeholder="gold engagement ring"
                className="h-12 w-full rounded-xl border border-line bg-ivory px-4 outline-none transition focus:border-gold"
              />
              <div className="mt-5 flex justify-center">
                <Button variant="primary" size="lg" onClick={() => go(text)}>
                  <Sparkles className="h-4 w-4" aria-hidden="true" />
                  {text.trim() ? "Find My Match" : "Find Similar Jewellery"}
                </Button>
              </div>
            </div>
          ) : (
            <div className="mt-8">
              <p className="mb-4 text-center text-sm text-muted">or describe what you're looking for</p>
              <SearchBar value={text} onChange={setText} onSubmit={go} placeholder="gold wedding necklace" label="Describe the jewellery you want" />
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
