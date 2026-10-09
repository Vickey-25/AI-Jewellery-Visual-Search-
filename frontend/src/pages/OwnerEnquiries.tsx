import {
  AlertCircle,
  CheckCircle,
  Clock,
  Crown,
  Filter,
  Mail,
  MessageSquare,
  Package,
  Phone,
  RefreshCw,
  Search,
  User,
  XCircle,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listOwnerEnquiries, updateEnquiryStatus } from "../api/enquiriesApi";
import { useAuth } from "../hooks/useAuth";
import type { Enquiry, EnquiryStatus } from "../types/enquiry";

export default function OwnerEnquiries() {
  const { isOwner, isAuthenticated } = useAuth();
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const fetchEnquiries = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listOwnerEnquiries(statusFilter, searchTerm);
      setEnquiries(res.items);
    } catch (err: any) {
      setError(err?.message || "Failed to load enquiries.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOwner) {
      fetchEnquiries();
    }
  }, [isOwner, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchEnquiries();
  };

  const handleStatusChange = async (enquiryId: number, newStatus: EnquiryStatus) => {
    setUpdatingId(enquiryId);
    try {
      const updated = await updateEnquiryStatus(enquiryId, newStatus);
      setEnquiries((prev) => prev.map((e) => (e.id === enquiryId ? { ...e, status: updated.status } : e)));
    } catch (err: any) {
      alert(err?.message || "Failed to update status.");
    } finally {
      setUpdatingId(null);
    }
  };

  if (!isAuthenticated || !isOwner) {
    return (
      <div className="container-page py-16 text-center">
        <div className="mx-auto max-w-md rounded-2xl border border-gold/30 bg-white/80 p-8 shadow-soft backdrop-blur-md">
          <Crown className="mx-auto h-12 w-12 text-gold-deep mb-3" />
          <h2 className="font-display text-2xl text-ink">Shop Owner Portal Required</h2>
          <p className="mt-2 text-sm text-charcoal/70">
            Please log in with a Shop Owner account to view customer enquiries and manage jewellery consultations.
          </p>
          <Link
            to="/login"
            className="mt-6 inline-block rounded-xl bg-ink px-6 py-3 text-xs font-semibold text-gold hover:bg-black transition shadow-md"
          >
            Sign In as Shop Owner
          </Link>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: EnquiryStatus) => {
    switch (status) {
      case "pending":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700 border border-amber-200">
            <Clock className="h-3.5 w-3.5 text-amber-500" /> Pending Review
          </span>
        );
      case "contacted":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700 border border-sky-200">
            <Mail className="h-3.5 w-3.5 text-sky-500" /> Client Contacted
          </span>
        );
      case "completed":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 border border-emerald-200">
            <CheckCircle className="h-3.5 w-3.5 text-emerald-500" /> Sale Completed
          </span>
        );
      case "cancelled":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-semibold text-gray-600 border border-gray-200">
            <XCircle className="h-3.5 w-3.5 text-gray-400" /> Cancelled
          </span>
        );
    }
  };

  return (
    <div className="container-page py-10 lg:py-14">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-line pb-6">
        <div>
          <div className="flex items-center gap-2 text-gold-deep text-xs font-semibold uppercase tracking-[0.25em]">
            <Crown className="h-4 w-4" /> Store Owner Dashboard
          </div>
          <h1 className="mt-1 font-display text-3xl font-light text-ink">Customer Jewellery Enquiries</h1>
          <p className="mt-1 text-xs text-charcoal/70">
            Review client requests, inspect selected jewellery pieces, and log consultation status updates.
          </p>
        </div>

        <button
          type="button"
          onClick={fetchEnquiries}
          className="flex items-center gap-2 rounded-xl border border-line bg-white px-4 py-2 text-xs font-semibold text-ink hover:bg-beige transition shadow-xs self-start md:self-auto"
        >
          <RefreshCw className={`h-4 w-4 text-gold-deep ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Enquiries</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="mt-6 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 rounded-xl bg-beige/40 p-4 border border-gold/20">
        {/* Status Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs font-semibold text-charcoal/70 mr-1 flex items-center gap-1">
            <Filter className="h-3.5 w-3.5" /> Status:
          </span>
          {["all", "pending", "contacted", "completed", "cancelled"].map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setStatusFilter(st)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold capitalize transition ${
                statusFilter === st
                  ? "bg-ink text-gold shadow-xs"
                  : "bg-white text-charcoal hover:bg-beige border border-line"
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-sm">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search client name, email, item..."
            className="w-full rounded-xl border border-line bg-white pl-9 pr-4 py-2 text-xs text-ink placeholder:text-charcoal/40 focus:border-gold focus:outline-none"
          />
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-charcoal/40" />
        </form>
      </div>

      {/* Content State */}
      {loading ? (
        <div className="py-20 text-center text-charcoal/60">
          <RefreshCw className="mx-auto h-8 w-8 animate-spin text-gold-deep mb-3" />
          <p className="text-xs font-medium">Fetching jewellery enquiries...</p>
        </div>
      ) : error ? (
        <div className="mt-8 rounded-xl bg-red-50 p-6 text-center text-red-700 text-sm border border-red-200">
          <AlertCircle className="mx-auto h-8 w-8 text-red-500 mb-2" />
          <p>{error}</p>
        </div>
      ) : enquiries.length === 0 ? (
        <div className="mt-10 rounded-2xl border border-dashed border-line bg-white/60 p-12 text-center">
          <MessageSquare className="mx-auto h-12 w-12 text-gold/60 mb-3" />
          <h3 className="font-display text-xl text-ink">No Customer Enquiries Found</h3>
          <p className="mt-1 text-xs text-charcoal/60">
            {statusFilter !== "all" || searchTerm
              ? "No enquiries match your current filter settings."
              : "When customers enquire about jewellery pieces, their requests will appear here."}
          </p>
        </div>
      ) : (
        <div className="mt-8 space-y-6">
          {enquiries.map((item) => (
            <div
              key={item.id}
              className="rounded-2xl border border-line bg-white p-6 shadow-soft transition hover:border-gold/40"
            >
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                {/* Left: Customer Info */}
                <div className="lg:col-span-4 space-y-3 border-b lg:border-b-0 lg:border-r border-line/80 pb-4 lg:pb-0 lg:pr-6">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-gold-deep uppercase tracking-wider">
                      Enquiry #{item.id}
                    </span>
                    <span className="text-[11px] text-charcoal/50">
                      {new Date(item.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>

                  <div>
                    <h4 className="flex items-center gap-2 font-display text-lg text-ink font-normal">
                      <User className="h-4 w-4 text-gold-deep shrink-0" />
                      <span>{item.name}</span>
                    </h4>
                    <p className="mt-1 flex items-center gap-2 text-xs text-charcoal/80">
                      <Mail className="h-3.5 w-3.5 text-charcoal/40 shrink-0" />
                      <a href={`mailto:${item.email}`} className="hover:text-gold-deep underline">
                        {item.email}
                      </a>
                    </p>
                    {item.phone && (
                      <p className="mt-1 flex items-center gap-2 text-xs text-charcoal/80">
                        <Phone className="h-3.5 w-3.5 text-charcoal/40 shrink-0" />
                        <a href={`tel:${item.phone}`} className="hover:text-gold-deep">
                          {item.phone}
                        </a>
                      </p>
                    )}
                  </div>

                  {item.message && (
                    <div className="rounded-xl bg-beige/40 p-3 text-xs text-charcoal/90 border border-gold/10 italic">
                      "{item.message}"
                    </div>
                  )}

                  {/* Status Dropdown */}
                  <div className="pt-2">
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-charcoal/60 mb-1">
                      Update Consultation Status
                    </label>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(item.status)}
                      <select
                        value={item.status}
                        disabled={updatingId === item.id}
                        onChange={(e) => handleStatusChange(item.id, e.target.value as EnquiryStatus)}
                        className="rounded-lg border border-line bg-beige/30 px-2.5 py-1 text-xs text-ink focus:border-gold focus:outline-none"
                      >
                        <option value="pending">Mark Pending</option>
                        <option value="contacted">Mark Contacted</option>
                        <option value="completed">Mark Completed</option>
                        <option value="cancelled">Mark Cancelled</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Right: Selected Jewellery Piece Details */}
                <div className="lg:col-span-8">
                  <div className="flex items-center gap-2 text-xs font-semibold text-charcoal/70 uppercase tracking-wider mb-3">
                    <Package className="h-4 w-4 text-gold-deep" /> Selected Jewellery Piece
                  </div>

                  {item.product ? (
                    <div className="flex flex-col sm:flex-row items-center gap-4 rounded-xl border border-gold/20 bg-ivory/60 p-4">
                      <div className="h-28 w-28 shrink-0 overflow-hidden rounded-lg border border-line bg-white">
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

                      <div className="flex-1 text-center sm:text-left space-y-1">
                        <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                          <span className="rounded bg-gold/15 px-2 py-0.5 text-[10px] font-semibold text-gold-deep uppercase">
                            {item.product.product_code}
                          </span>
                          <span className="text-xs text-charcoal/60">{item.product.category}</span>
                        </div>

                        <h5 className="font-display text-base text-ink font-normal">{item.product.name}</h5>
                        <p className="text-xs text-charcoal/70">
                          {item.product.material} {item.product.purity ? `• ${item.product.purity}` : ""}{" "}
                          {item.product.stone_type ? `• ${item.product.stone_type}` : ""}
                        </p>

                        <div className="pt-1 flex items-center justify-between">
                          <span className="font-display text-lg font-medium text-gold-deep">
                            ${item.product.price.toLocaleString()}
                          </span>
                          <Link
                            to={`/products/${item.product.id}`}
                            className="text-xs font-semibold text-ink underline hover:text-gold-deep"
                          >
                            View Product & AI Similar →
                          </Link>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-xl bg-beige/30 p-4 text-xs text-charcoal/60">
                      Product ID #{item.product_id} (Item details unavailable or removed)
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
