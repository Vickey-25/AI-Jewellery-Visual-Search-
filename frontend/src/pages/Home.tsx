import BrandStory from "../components/home/BrandStory";
import Collections from "../components/home/Collections";
import Hero from "../components/home/Hero";
import HowItWorks from "../components/home/HowItWorks";
import VisualSearchSection from "../components/search/VisualSearchSection";

export default function Home() {
  return (
    <>
      <Hero />
      <VisualSearchSection />
      <Collections />
      <BrandStory />
      <HowItWorks />
    </>
  );
}
