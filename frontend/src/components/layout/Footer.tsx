import { Link } from "react-router-dom";

const colTitle = "text-xs font-medium uppercase tracking-[0.2em] text-gold";
const link = "text-sm text-ivory/70 transition hover:text-gold";

export default function Footer() {
  return (
    <footer className="mt-24 bg-dark text-ivory">
      <div className="container-page grid gap-12 py-16 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div>
          <p className="font-display text-2xl tracking-[0.28em]">LUMIÈRE</p>
          <p className="mt-1.5 text-[10px] font-medium tracking-[0.42em] text-gold">AI JEWELLERY</p>
          <p className="mt-6 max-w-xs text-sm leading-relaxed text-ivory/70">Discover jewellery through a new lens.</p>
        </div>
        <nav aria-label="Discover">
          <p className={colTitle}>Discover</p>
          <ul className="mt-5 space-y-3">
            <li><Link className={link} to="/search">Visual Search</Link></li>
            <li><Link className={link} to="/products">Collection</Link></li>
            <li><Link className={link} to="/#collections">Collections</Link></li>
            <li><Link className={link} to="/about">About</Link></li>
          </ul>
        </nav>
        <nav aria-label="Customer care">
          <p className={colTitle}>Customer Care</p>
          <ul className="mt-5 space-y-3">
            <li><Link className={link} to="/about#contact">Contact</Link></li>
            <li><Link className={link} to="/about#shipping">Shipping</Link></li>
            <li><Link className={link} to="/about#returns">Returns</Link></li>
          </ul>
        </nav>
        <nav aria-label="Follow">
          <p className={colTitle}>Follow</p>
          <ul className="mt-5 space-y-3">
            {[
              ["Instagram", "https://www.instagram.com/"],
              ["Pinterest", "https://www.pinterest.com/"],
              ["Facebook", "https://www.facebook.com/"],
            ].map(([name, href]) => (
              <li key={name}>
                <a className={link} href={href} target="_blank" rel="noopener noreferrer">
                  {name}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
      <div className="border-t border-ivory/10">
        <div className="container-page flex flex-col items-center justify-between gap-3 py-6 text-xs text-ivory/60 sm:flex-row">
          <p>© 2026 Lumière AI Jewellery</p>
          <p>
            <Link className="hover:text-gold" to="/about#privacy">Privacy</Link>
            {" · "}
            <Link className="hover:text-gold" to="/about#terms">Terms</Link>
          </p>
        </div>
      </div>
    </footer>
  );
}
