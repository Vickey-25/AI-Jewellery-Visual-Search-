import type { SearchResult } from "../types";
import ProductCard from "./ProductCard";

interface Props {
  results: SearchResult[];
  onSelect: (productId: number) => void;
  title?: string;
}

export default function SearchResults({ results, onSelect, title = "Similar Jewellery" }: Props) {
  if (results.length === 0) {
    return (
      <div className="empty">
        <p className="empty-title">No similar jewellery found.</p>
        <p>Try a clearer photo of a single piece, or clear the filters.</p>
      </div>
    );
  }
  return (
    <>
      <div className="results-head">
        <h2>{title}</h2>
        <p>Similarity is a ranking score from the AI model, not a probability.</p>
      </div>
      <div className="grid">
        {results.map((r) => (
          <ProductCard key={r.product_id} result={r} onSelect={onSelect} />
        ))}
      </div>
    </>
  );
}
