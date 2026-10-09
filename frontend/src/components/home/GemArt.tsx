/** Original line-art gem used in the hero. Pure SVG, so there is no external asset to depend on. */
export default function GemArt({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 400 400" className={className} fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="gem-gold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#E9D9B4" />
          <stop offset="0.5" stopColor="#C9A45C" />
          <stop offset="1" stopColor="#8A6A24" />
        </linearGradient>
        <radialGradient id="gem-glow" cx="0.5" cy="0.45" r="0.5">
          <stop offset="0" stopColor="#F3EBDA" />
          <stop offset="1" stopColor="#FAF8F4" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="200" cy="200" r="190" fill="url(#gem-glow)" />
      <circle cx="200" cy="200" r="150" stroke="#C9A45C" strokeOpacity="0.35" strokeDasharray="2 7" />
      <circle cx="200" cy="200" r="115" stroke="#C9A45C" strokeOpacity="0.5" />
      <g stroke="url(#gem-gold)" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" fill="#C9A45C" fillOpacity="0.07">
        <path d="M130 140h140l50 60-120 130L80 200z" />
        <path d="M80 200h240M170 200l30 130 30-130M130 140l40 60 30-60 30 60 40-60M200 140v60" fill="none" />
      </g>
      <g fill="#C9A45C">
        <circle cx="330" cy="110" r="3" />
        <circle cx="62" cy="268" r="2.4" />
        <path d="M335 300l3 9 9 3-9 3-3 9-3-9-9-3 9-3z" />
        <path d="M70 110l2 6 6 2-6 2-2 6-2-6-6-2 6-2z" />
      </g>
    </svg>
  );
}
