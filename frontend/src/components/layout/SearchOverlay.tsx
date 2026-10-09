import { ImagePlus, X } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import SearchBar from "../search/SearchBar";
import Modal from "../ui/Modal";

const IDEAS = ["gold wedding necklace", "diamond ring for engagement", "silver daily wear earrings"];

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function SearchOverlay({ open, onClose }: Props) {
  const [text, setText] = useState("");
  const navigate = useNavigate();

  const go = (value: string) => {
    if (!value) return;
    onClose();
    navigate(`/search?q=${encodeURIComponent(value)}`);
  };

  return (
    <Modal open={open} onClose={onClose} label="Search jewellery" placement="top">
      <div className="p-5 sm:p-7">
        <div className="flex items-center gap-3">
          <SearchBar
            value={text}
            onChange={setText}
            onSubmit={go}
            size="lg"
            placeholder="Describe what you're looking for"
            className="flex-1"
          />
          <button type="button" onClick={onClose} aria-label="Close search" className="rounded-lg p-2 text-muted hover:bg-beige hover:text-ink">
            <X className="h-5 w-5" />
          </button>
        </div>
        <p className="mt-5 text-sm text-muted">Try</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {IDEAS.map((idea) => (
            <button
              key={idea}
              type="button"
              onClick={() => go(idea)}
              className="rounded-lg border border-line bg-surface px-3 py-1.5 text-sm transition hover:border-gold"
            >
              {idea}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={() => {
            onClose();
            navigate("/search");
          }}
          className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-gold-deep hover:underline"
        >
          <ImagePlus className="h-4 w-4" /> Or search with a photo
        </button>
      </div>
    </Modal>
  );
}
