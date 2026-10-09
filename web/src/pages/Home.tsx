import { useEffect, useRef, useState } from "react";
import Filters from "../components/Filters";
import ImageUploader from "../components/ImageUploader";
import Loading from "../components/Loading";
import ProductDetails from "../components/ProductDetails";
import SearchResults from "../components/SearchResults";
import { ApiRequestError, getFacets, searchByImage } from "../services/api";
import type { Facets, SearchFilters, SearchResult } from "../types";

export default function Home() {
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [facets, setFacets] = useState<Facets | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const resultsRef = useRef<HTMLElement>(null);

  useEffect(() => {
    getFacets().then(setFacets).catch(() => setFacets(null));
  }, []);

  async function handleSearch(file: File) {
    setLoading(true);
    setError(null);
    try {
      const response = await searchByImage(file, filters, 6);
      setResults(response.results);
      requestAnimationFrame(() =>
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
      );
    } catch (err) {
      setResults(null);
      setError(
        err instanceof ApiRequestError ? err.message : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <p className="brand">
          <span aria-hidden="true">💎</span> AI Jewellery Search
        </p>
        <h1>Find similar jewellery using AI.</h1>
        <p className="lede">
          Upload a photo of a necklace, ring, earrings or any piece. We match it to the closest
          designs in our catalogue.
        </p>
      </header>

      <ImageUploader loading={loading} onSearch={handleSearch} serverError={error} />
      {facets && <Filters facets={facets} value={filters} onChange={setFilters} />}

      <main ref={resultsRef} className="results" aria-live="polite">
        {loading && <Loading />}
        {!loading && results && <SearchResults results={results} onSelect={setSelectedId} />}
      </main>

      <footer className="footer">
        Search runs on a local open-source model. Uploaded photos are not stored.
      </footer>

      {selectedId !== null && (
        <ProductDetails
          productId={selectedId}
          onClose={() => setSelectedId(null)}
          onSelect={setSelectedId}
        />
      )}
    </div>
  );
}
