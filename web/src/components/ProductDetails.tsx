import { useEffect, useState } from "react";
import { formatPrice } from "../format";
import { ApiRequestError, getProduct, getSimilarProducts, imageUrl, enquireProduct } from "../services/api";
import type { Product, SearchResult } from "../types";
import Loading from "./Loading";
import SearchResults from "./SearchResults";

interface Props {
  productId: number;
  onClose: () => void;
  onSelect: (productId: number) => void;
}

function messageFrom(err: unknown): string {
  return err instanceof ApiRequestError ? err.message : "Something went wrong. Please try again.";
}

export default function ProductDetails({ productId, onClose, onSelect }: Props) {
  const [product, setProduct] = useState<Product | null>(null);
  const [similar, setSimilar] = useState<SearchResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [similarError, setSimilarError] = useState<string | null>(null);
  const [showEnquire, setShowEnquire] = useState(false);
  const [enquireName, setEnquireName] = useState("");
  const [enquireEmail, setEnquireEmail] = useState("");
  const [enquireMessage, setEnquireMessage] = useState("");
  const [enquireStatus, setEnquireStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [enquireError, setEnquireError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setProduct(null);
    setSimilar(null);
    setError(null);
    setSimilarError(null);
    getProduct(productId)
      .then((p) => !cancelled && setProduct(p))
      .catch((e) => !cancelled && setError(messageFrom(e)));
    getSimilarProducts(productId, 4)
      .then((r) => !cancelled && setSimilar(r.results))
      .catch((e) => !cancelled && setSimilarError(messageFrom(e)));
    return () => {
      cancelled = true;
    };
  }, [productId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const rows: [string, string | null][] = product
    ? [
      ["Product code", product.product_code],
      ["Category", product.category],
      ["Material", product.material],
      ["Purity", product.purity],
      ["Weight", product.weight !== null ? `${product.weight} g` : null],
      ["Stone type", product.stone_type],
      ["Colour", product.colour],
      ["Occasion", product.occasion],
    ]
    : [];

  const handleEnquire = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!product) return;
    setEnquireStatus("submitting");
    setEnquireError(null);
    try {
      await enquireProduct(product.id, {
        name: enquireName,
        email: enquireEmail,
        message: enquireMessage,
      });
      setEnquireStatus("success");
    } catch (err) {
      setEnquireStatus("error");
      setEnquireError(messageFrom(err));
    }
  };

  return (
    <div className="overlay" onClick={onClose}>
      <div
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-label={product?.name ?? "Product details"}
        onClick={(e) => e.stopPropagation()}
      >
        <button type="button" className="dialog-close" onClick={onClose} aria-label="Close details">
          Close
        </button>

        {error && <p className="tray-error dark-on-light" role="alert">{error}</p>}
        {!product && !error && <Loading title="Loading product..." detail="" />}

        {product && (
          <>
            <div className="detail">
              <img className="detail-image" src={imageUrl(product.image_url)} alt={product.name} />
              <div>
                <h2 className="detail-name">{product.name}</h2>
                <p className="detail-price">{formatPrice(product.price)}</p>
                <dl className="specs">
                  {rows
                    .filter(([, v]) => v)
                    .map(([k, v]) => (
                      <div key={k} className="spec">
                        <dt>{k}</dt>
                        <dd>{v}</dd>
                      </div>
                    ))}
                </dl>
                {product.description && <p className="detail-desc">{product.description}</p>}

                <div style={{ marginTop: "1rem" }}>
                  {!showEnquire ? (
                    <button type="button" className="button button-primary" onClick={(e) => { e.preventDefault(); e.stopPropagation(); console.log("Enquire clicked"); setShowEnquire(true); }}>Enquire About This Item</button>
                  ) : enquireStatus === "success" ? (
                    <div style={{ padding: "1rem", backgroundColor: "#e6fffa", color: "#234e52", borderRadius: "4px" }}>
                      Thank you! Your enquiry has been sent. We will get back to you shortly.
                    </div>
                  ) : (
                    <form onSubmit={handleEnquire} style={{ display: "flex", flexDirection: "column", gap: "0.5rem", padding: "1rem", backgroundColor: "#f7fafc", borderRadius: "4px" }}>
                      <h3 style={{ margin: 0, fontSize: "1.1rem" }}>Enquire</h3>
                      {enquireError && <div style={{ color: "red" }}>{enquireError}</div>}
                      <input type="text" placeholder="Your Name" required value={enquireName} onChange={e => setEnquireName(e.target.value)} className="input" />
                      <input type="email" placeholder="Your Email" required value={enquireEmail} onChange={e => setEnquireEmail(e.target.value)} className="input" />
                      <textarea placeholder="Message (optional)" value={enquireMessage} onChange={e => setEnquireMessage(e.target.value)} className="input" style={{ minHeight: "80px" }} />
                      <div style={{ display: "flex", gap: "0.5rem" }}>
                        <button type="submit" className="button button-primary" disabled={enquireStatus === "submitting"}>
                          {enquireStatus === "submitting" ? "Sending..." : "Submit Enquiry"}
                        </button>
                        <button type="button" className="button" onClick={() => setShowEnquire(false)}>Cancel</button>
                      </div>
                    </form>
                  )}
                </div>
              </div>
            </div>

            <div className="detail-similar">
              {similar === null && !similarError && (
                <Loading title="Finding similar pieces..." detail="" />
              )}
              {similarError && <p className="muted">{similarError}</p>}
              {similar && (
                <SearchResults results={similar} onSelect={onSelect} title="Similar Jewellery" />
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
