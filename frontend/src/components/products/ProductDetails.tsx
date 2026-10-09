import { useEffect, useState } from "react";
import { CheckCircle2, Loader2, Mail, Send, X } from "lucide-react";
import { formatCurrency } from "../../utils/formatCurrency";
import type { Product } from "../../types/product";
import { buttonClasses } from "../ui/buttonStyles";
import Modal from "../ui/Modal";
import ProductImage from "./ProductImage";
import WishlistButton from "./WishlistButton";
import { enquireProduct } from "../../api/productsApi";
import { useAuth } from "../../hooks/useAuth";

export default function ProductDetails({ product }: { product: Product }) {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState(user?.full_name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [message, setMessage] = useState(
    `Hello, I would like to enquire about the price, availability, and details for "${product.name}" (Code: ${product.product_code}).`
  );
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      if (!name) setName(user.full_name);
      if (!email) setEmail(user.email);
    }
  }, [user]);

  const specs: [string, string | null][] = [
    ["Category", product.category],
    ["Material", product.material],
    ["Purity", product.purity],
    ["Weight", product.weight !== null ? `${product.weight} g` : null],
    ["Stone", product.stone_type],
    ["Colour", product.colour],
    ["Occasion", product.occasion],
  ];

  const handleOpen = () => {
    if (user) {
      setName(user.full_name);
      setEmail(user.email);
    }
    setIsOpen(true);
    setStatus("idle");
    setErrorMessage(null);
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) {
      setErrorMessage("Please provide both your name and email.");
      return;
    }

    setStatus("submitting");
    setErrorMessage(null);

    try {
      await enquireProduct(product.id, {
        name: name.trim(),
        email: email.trim(),
        message: message.trim(),
      });
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrorMessage(
        err instanceof Error ? err.message : "Unable to send enquiry. Please check your connection and try again."
      );
    }
  };

  return (
    <>
      <div className="grid gap-10 lg:grid-cols-2 lg:gap-16">
        <div className="group overflow-hidden rounded-2xl border border-line bg-beige shadow-soft lg:sticky lg:top-28 lg:self-start">
          <div className="aspect-square overflow-hidden">
            <ProductImage
              src={product.image_url}
              alt={product.name}
              size={900}
              priority
              className="transition-transform duration-700 ease-out group-hover:scale-105"
            />
          </div>
        </div>

        <div className="animate-fade-up">
          <p className="eyebrow">{product.category}</p>
          <h1 className="mt-3 font-display text-4xl leading-tight sm:text-5xl">{product.name}</h1>
          <p className="mt-2 text-sm tracking-wide text-muted">Product code {product.product_code}</p>
          <p className="mt-6 text-3xl font-medium">{formatCurrency(product.price)}</p>

          <dl className="mt-8 border-t border-line">
            {specs
              .filter(([, v]) => v)
              .map(([label, value]) => (
                <div key={label} className="flex justify-between gap-6 border-b border-line py-3.5">
                  <dt className="text-muted">{label}</dt>
                  <dd className="text-right font-medium">{value}</dd>
                </div>
              ))}
          </dl>

          {product.description && <p className="mt-8 max-w-prose leading-relaxed text-muted">{product.description}</p>}

          <div className="mt-10 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={handleOpen}
              className={buttonClasses("primary", "lg", "flex-1")}
            >
              <Mail className="h-4 w-4" aria-hidden="true" />
              Enquire About This Piece
            </button>
            <WishlistButton productId={product.id} productName={product.name} variant="full" />
          </div>
        </div>
      </div>

      <Modal open={isOpen} onClose={handleClose} label="Enquire about jewellery">
        <div className="relative p-6 sm:p-8">
          <button
            type="button"
            onClick={handleClose}
            aria-label="Close dialog"
            className="absolute right-5 top-5 rounded-full p-2 text-muted hover:bg-beige hover:text-ink transition"
          >
            <X className="h-5 w-5" />
          </button>

          {status === "success" ? (
            <div className="text-center py-6 animate-fade-in">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <h2 className="font-display text-2xl">Enquiry Received</h2>
              <p className="mt-3 text-muted leading-relaxed">
                Thank you, <span className="font-semibold text-ink">{name}</span>! We have received your inquiry for{" "}
                <span className="font-medium text-ink">{product.name}</span>. Our jewellery specialist will be in touch
                at <span className="font-medium text-ink">{email}</span> shortly.
              </p>
              <div className="mt-8">
                <button
                  type="button"
                  onClick={handleClose}
                  className={buttonClasses("primary", "md", "w-full")}
                >
                  Done
                </button>
              </div>
            </div>
          ) : (
            <div>
              <div className="border-b border-line pb-4">
                <p className="eyebrow">Price & Availability</p>
                <h2 className="mt-1 font-display text-2xl sm:text-3xl">Enquire About This Piece</h2>
                <div className="mt-2 flex items-center justify-between text-sm text-muted">
                  <span className="font-medium text-ink">{product.name}</span>
                  <span className="font-semibold text-gold-deep">{formatCurrency(product.price)}</span>
                </div>
              </div>

              {errorMessage && (
                <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {errorMessage}
                </div>
              )}

              <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                <div>
                  <label htmlFor="enquiry-name" className="block text-xs font-semibold uppercase tracking-wider text-muted">
                    Full Name *
                  </label>
                  <input
                    id="enquiry-name"
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Jane Doe"
                    className="mt-1.5 w-full rounded-xl border border-line bg-surface px-4 py-2.5 text-sm text-ink placeholder:text-muted/60 focus:border-gold focus:outline-none transition shadow-soft"
                  />
                </div>

                <div>
                  <label htmlFor="enquiry-email" className="block text-xs font-semibold uppercase tracking-wider text-muted">
                    Email Address *
                  </label>
                  <input
                    id="enquiry-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g. jane@example.com"
                    className="mt-1.5 w-full rounded-xl border border-line bg-surface px-4 py-2.5 text-sm text-ink placeholder:text-muted/60 focus:border-gold focus:outline-none transition shadow-soft"
                  />
                </div>

                <div>
                  <label htmlFor="enquiry-message" className="block text-xs font-semibold uppercase tracking-wider text-muted">
                    Message / Special Requests
                  </label>
                  <textarea
                    id="enquiry-message"
                    rows={4}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    className="mt-1.5 w-full rounded-xl border border-line bg-surface p-4 text-sm text-ink placeholder:text-muted/60 focus:border-gold focus:outline-none transition shadow-soft resize-none"
                  />
                </div>

                <div className="pt-2 flex gap-3">
                  <button
                    type="button"
                    onClick={handleClose}
                    className={buttonClasses("outline", "md", "flex-1")}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={status === "submitting"}
                    className={buttonClasses("primary", "md", "flex-1 flex items-center justify-center gap-2")}
                  >
                    {status === "submitting" ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send className="h-4 w-4" />
                        Send Enquiry
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </Modal>
    </>
  );
}

