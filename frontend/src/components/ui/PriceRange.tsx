import { formatCurrency } from "../../utils/formatCurrency";

interface Props {
  min: number;
  max: number;
  step?: number;
  value: [number, number];
  onChange: (value: [number, number]) => void;
}

export default function PriceRange({ min, max, step = 1000, value, onChange }: Props) {
  const [lo, hi] = value;
  const pct = (v: number) => ((v - min) / Math.max(1, max - min)) * 100;

  return (
    <div>
      <div className="range-dual relative h-5">
        <div className="absolute inset-x-0 top-1/2 h-0.5 -translate-y-1/2 rounded bg-line" />
        <div
          className="absolute top-1/2 h-0.5 -translate-y-1/2 rounded bg-gold"
          style={{ left: `${pct(lo)}%`, right: `${100 - pct(hi)}%` }}
        />
        <input
          type="range"
          aria-label="Minimum price"
          min={min}
          max={max}
          step={step}
          value={lo}
          onChange={(e) => onChange([Math.min(Number(e.target.value), hi - step), hi])}
        />
        <input
          type="range"
          aria-label="Maximum price"
          min={min}
          max={max}
          step={step}
          value={hi}
          onChange={(e) => onChange([lo, Math.max(Number(e.target.value), lo + step)])}
        />
      </div>
      <div className="mt-3 flex justify-between text-sm text-muted">
        <span>{formatCurrency(lo)}</span>
        <span>{formatCurrency(hi)}</span>
      </div>
    </div>
  );
}
