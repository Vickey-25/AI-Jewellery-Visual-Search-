import { AlertCircle, CheckCircle, Clock, Mail, MessageSquare, Package, RefreshCw, User, XCircle } from "lucide-react";
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listCustomerEnquiries } from "../api/enquiriesApi";
import { useAuth } from "../hooks/useAuth";
import type { Enquiry } from "../types/enquiry";

export default function CustomerEnquiries() {
  const { isAuthenticated, user } = useAuth();
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEnquiries = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listCustomerEnquiries();
      setEnquiries(res.items);
    } catch (err: any) {
      setError(err?.message || "Failed to load your enquiries.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchEnquiries();
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="container-page py-16 text-center">
        <div className="mx-auto max-w-md rounded-2xl border border-gold/30 bg-white/80 p-8 shadow-soft backdrop-blur-md">
          <User className="mx-auto h-12 w-12 text-gold-deep mb-3" />
          <h2 className="font-display text-2xl text-ink">Sign In to Track Enquiries</h2>
          <p className="mt-2 text-sm text-charcoal/70">
            Please log in with your client account to view status updates on your jewellery consultations.
          </p>
          <Link
            to="/login"
            className="mt-6 inline-block rounded-xl bg-gold px-6 py-3 text-xs font-semibold text-dark hover:bg-gold-deep transition shadow-md"
          >
            Sign In / Register
          </Link>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pending":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700 border border-amber-200">
            <Clock className="h-3.5 w-3.5 text-amber-500" /> Under Master Jeweller Review
          </span>
        );
      case "contacted":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700 border border-sky-200">
            <Mail className="h-3.5 w-3.5 text-sky-500" /> Jeweller Contacted You
          </span>
        );
      case "completed":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 border border-emerald-200">
            <CheckCircle className="h-3.5 w-3.5 text-emerald-500" /> Consultation Completed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-semibold text-gray-600 border border-gray-200">
            <XCircle className="h-3.5 w-3.5 text-gray-400" /> Closed
          </span>
        );
    }
  };

  return (
    <div className="container-page py-10 lg:py-14">
      <div className="flex items-center justify-between border-b border-line pb-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-deep">Client Portal</span>
          <h1 className="mt-1 font-display text-3xl font-light text-ink">My Jewellery Enquiries</h1>
          <p className="mt-1 text-xs text-charcoal/70">
            Track status and details of your consultations with Lumière master jewellers.
          </p>
        </div>

        <button
          type="button"
          onClick={fetchEnquiries}
          className="flex items-center gap-2 rounded-xl border border-line bg-white px-4 py-2 text-xs font-semibold text-ink hover:bg-beige transition"
        >
          <RefreshCw className={`h-4 w-4 text-gold-deep ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {loading ? (
        <div className="py-20 text-center text-charcoal/60">
          <RefreshCw className="mx-auto h-8 w-8 animate-spin text-gold-deep mb-3" />
          <p className="text-xs font-medium">Retrieving your requests...</p>
        </div>
      ) : error ? (
        <div className="mt-8 rounded-xl bg-red-50 p-6 text-center text-red-700 text-sm border border-red-200">
          <AlertCircle className="mx-auto h-8 w-8 text-red-500 mb-2" />
          <p>{error}</p>
        </div>
      ) : enquiries.length === 0 ? (
        <div className="mt-10 rounded-2xl border border-dashed border-line bg-white/60 p-12 text-center">
          <MessageSquare className="mx-auto h-12 w-12 text-gold/60 mb-3" />
          <h3 className="font-display text-xl text-ink">No Enquiries Yet</h3>
          <p className="mt-1 text-xs text-charcoal/60 mb-6">
            Browse our catalogue or perform an AI visual search to enquire about any bespoke piece.
          </p>
          <Link
            to="/products"
            className="rounded-xl bg-gold px-6 py-3 text-xs font-semibold text-dark hover:bg-gold-deep transition shadow-md"
          >
            Explore Catalogue
          </Link>
        </div>
      ) : (
        <div className="mt-8 space-y-6">
          {enquiries.map((item) => (
            <div key={item.id} className="rounded-2xl border border-line bg-white p-6 shadow-soft">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-line/60 pb-4 mb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-gold-deep uppercase">Enquiry #{item.id}</span>
                    <span className="text-xs text-charcoal/40">•</span>
                    <span className="text-xs text-charcoal/60">
                      {new Date(item.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </span>
                  </div>
                </div>

                <div>{getStatusBadge(item.status)}</div>
              </div>

              {item.product && (
                <div className="flex flex-col sm:flex-row items-center gap-4 rounded-xl border border-gold/20 bg-ivory/60 p-4">
                  <div className="h-24 w-24 shrink-0 overflow-hidden rounded-lg border border-line bg-white">
                    <img
                      src={item.product.image_url || "/placeholder-jewel.jpg"}
                      alt={item.product.name}
                      className="h-full w-full object-cover"
                      onError={(e) => {
                        (e.currentTarget as HTMLImageElement).src =
                          "https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=300&q=80";
                      }}
                    />
                  </div>

                  <div className="flex-1 text-center sm:text-left">
                    <span className="text-[10px] font-semibold uppercase text-gold-deep">
                      {item.product.product_code}
                    </span>
                    <h4 className="font-display text-base text-ink font-normal">{item.product.name}</h4>
                    <p className="text-xs text-charcoal/70">{item.product.category} • ${item.product.price.toLocaleString()}</p>
                    <Link
                      to={`/products/${item.product.id}`}
                      className="mt-2 inline-block text-xs font-semibold text-ink underline hover:text-gold-deep"
                    >
                      View Piece Details →
                    </Link>
                  </div>
                </div>
              )}

              {item.message && (
                <div className="mt-4 rounded-xl bg-beige/30 p-3 text-xs text-charcoal/80 italic">
                  <strong>Your note:</strong> "{item.message}"
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
