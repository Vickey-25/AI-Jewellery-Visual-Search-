import { ENQUIRY_EMAIL } from "../config";
import { ButtonLink } from "../components/ui/Button";

const section = "scroll-mt-28 border-t border-line pt-10";

export default function About() {
  return (
    <div className="container-page max-w-4xl py-12 sm:py-20">
      <p className="eyebrow">About</p>
      <h1 className="mt-4 text-4xl leading-tight sm:text-6xl">Jewellery, discovered differently.</h1>
      <p className="mt-8 max-w-2xl text-lg leading-relaxed text-muted">
        Lumière pairs the craft of fine jewellery with visual search. Instead of hunting through categories, show us
        what catches your eye and we'll find the pieces in our collection that share its look and feel.
      </p>

      <div className="mt-16 space-y-14">
        <section id="how-it-works" className={section} aria-labelledby="about-ai">
          <h2 id="about-ai" className="font-display text-2xl">How visual search works</h2>
          <p className="mt-4 max-w-2xl leading-relaxed text-muted">
            When you upload a photo, our AI studies its shape, style and detail and compares it with every piece in the
            collection. The percentage you see on a result is how closely a piece resembles your image. It is a guide
            to visual similarity, not a guarantee, so it's a starting point for discovery.
          </p>
        </section>

        <section id="contact" className={section} aria-labelledby="about-contact">
          <h2 id="about-contact" className="font-display text-2xl">Contact</h2>
          <p className="mt-4 text-muted">
            Questions about a piece? Write to{" "}
            <a className="font-medium text-gold-deep underline underline-offset-4" href={`mailto:${ENQUIRY_EMAIL}`}>{ENQUIRY_EMAIL}</a>.
          </p>
        </section>

        <section id="shipping" className={section} aria-labelledby="about-shipping">
          <h2 id="about-shipping" className="font-display text-2xl">Shipping</h2>
          <p className="mt-4 text-muted">This is a demonstration storefront. Shipping details will be published here before launch.</p>
        </section>

        <section id="returns" className={section} aria-labelledby="about-returns">
          <h2 id="about-returns" className="font-display text-2xl">Returns</h2>
          <p className="mt-4 text-muted">This is a demonstration storefront. Returns information will be published here before launch.</p>
        </section>

        <section id="privacy" className={section} aria-labelledby="about-privacy">
          <h2 id="about-privacy" className="font-display text-2xl">Privacy</h2>
          <p className="mt-4 text-muted">
            Photos you upload for search are analysed to find matches and are not stored. Your wishlist is kept only in
            your own browser.
          </p>
        </section>

        <section id="terms" className={section} aria-labelledby="about-terms">
          <h2 id="about-terms" className="font-display text-2xl">Terms</h2>
          <p className="mt-4 text-muted">Product names, prices and descriptions in this demonstration are fictional.</p>
        </section>
      </div>

      <div className="mt-16 flex gap-3">
        <ButtonLink to="/search" variant="primary" size="lg">Find My Jewellery</ButtonLink>
        <ButtonLink to="/products" variant="outline" size="lg">Explore Collection</ButtonLink>
      </div>
    </div>
  );
}
