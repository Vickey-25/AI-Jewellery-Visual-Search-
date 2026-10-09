const STEPS = [
  { n: "01", title: "Upload", text: "Share an image of jewellery you love." },
  { n: "02", title: "AI Understands", text: "Our visual search engine analyzes its design." },
  { n: "03", title: "Discover", text: "Explore visually similar pieces from the collection." },
];

export default function HowItWorks() {
  return (
    <section className="container-page py-20 sm:py-28" aria-labelledby="how-heading">
      <div className="max-w-xl">
        <p className="eyebrow">How it works</p>
        <h2 id="how-heading" className="section-title mt-3">Three quiet steps</h2>
      </div>
      <ol className="mt-12 grid gap-10 md:grid-cols-3">
        {STEPS.map((s) => (
          <li key={s.n} className="border-t border-gold/50 pt-6">
            <span className="font-display text-5xl text-gold/70">{s.n}</span>
            <h3 className="mt-4 font-display text-2xl">{s.title}</h3>
            <p className="mt-2 text-muted">{s.text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
