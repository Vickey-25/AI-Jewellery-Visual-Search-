import { formatPercent, formatPrice } from "../format";
import { imageUrl } from "../services/api";
import type { SearchResult } from "../types";

interface Props {
  result: SearchResult;
  onSelect: (productId: number) => void;
}

export default function ProductCard({ result, onSelect }: Props) {
  const percent = formatPercent(result.similarity);
  const spec = [result.purity, result.material].filter(Boolean).join(" ");
  return (
    <button type="button" className="card" onClick={() => onSelect(result.product_id)}>
      <span className="card-media">
        <img src={imageUrl(result.image_url)} alt={result.name} loading="lazy" />
      </span>
      <span className="card-body">
        <span className="card-name">{result.name}</span>
        <span className="card-spec">{spec}</span>
        <span className="card-price">{formatPrice(result.price)}</span>
        <span className="card-score">
          <span className="card-score-label">
            Visual similarity <strong>{percent}</strong>
          </span>
          <span className="meter" aria-hidden="true">
            <span className="meter-fill" style={{ width: percent }} />
          </span>
        </span>
      </span>
    </button>
  );
}
