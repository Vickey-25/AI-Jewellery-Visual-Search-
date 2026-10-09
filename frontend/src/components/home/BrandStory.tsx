import { Camera, Heart, Sparkles } from "lucide-react";

const FEATURES = [
  { icon: Camera, title: "Visual Discovery", text: "Upload an image and discover similar designs." },
  { icon: Sparkles, title: "Intelligent Matching", text: "AI understands visual characteristics and finds relevant pieces." },
  { icon: Heart, title: "Personalised Exploration", text: "Explore jewellery that matches your style and occasion." },
];

export default function BrandStory() {
  return (
    <section className="bg-dark py-20 text-ivory sm:py-28" aria-labelledby="story-heading">
      <div className="container-page grid gap-14 lg:grid-cols-2 lg:gap-20">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.22em] text-gold">Our story</p>
          <h2 id="story-heading" className="mt-4 font-display text-4xl leading-tight sm:text-5xl">
            Jewellery, discovered differently.
          </h2>
          <p className="mt-6 max-w-md text-lg leading-relaxed text-ivory/70">
            Our AI visual search helps you discover jewellery based on what catches your eye, not just what you can describe.
          </p>
        </div>
        <ul className="space-y-8">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <li key={title} className="flex gap-5 border-b border-ivory/10 pb-8 last:border-0 last:pb-0">
              <span className="flex h-12 w-12 flex-none items-center justify-center rounded-full border border-gold/50 text-gold">
                <Icon className="h-5 w-5" strokeWidth={1.4} aria-hidden="true" />
              </span>
              <div>
                <h3 className="font-display text-xl">{title}</h3>
                <p className="mt-1.5 text-ivory/70">{text}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
