import { AlertCircle, CheckCircle2, Image as ImageIcon, Plus, Upload, X } from "lucide-react";
import React, { useState } from "react";
import { createProduct } from "../../api/productsApi";
import type { Product } from "../../types/product";

interface AddProductModalProps {
  open: boolean;
  onClose: () => void;
  onProductAdded?: (product: Product) => void;
}

export default function AddProductModal({ open, onClose, onProductAdded }: AddProductModalProps) {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [category, setCategory] = useState("Rings");
  const [material, setMaterial] = useState("Gold");
  const [price, setPrice] = useState("");
  const [purity, setPurity] = useState("22K Gold");
  const [weight, setWeight] = useState("");
  const [stoneType, setStoneType] = useState("Diamond");
  const [colour, setColour] = useState("Yellow Gold");
  const [occasion, setOccasion] = useState("Wedding");
  const [productCode, setProductCode] = useState("");
  const [description, setDescription] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  if (!open) return null;

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const url = URL.createObjectURL(file);
      setImagePreview(url);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!imageFile) {
      setError("Please select a high-resolution photo of the jewellery item.");
      return;
    }

    if (!name.trim() || !price || Number(price) <= 0) {
      setError("Please provide a valid product name and price.");
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("image", imageFile);
      formData.append("name", name.trim());
      formData.append("category", category.trim());
      formData.append("material", material.trim());
      formData.append("price", String(Number(price)));

      if (purity.trim()) formData.append("purity", purity.trim());
      if (weight && Number(weight) > 0) formData.append("weight", String(Number(weight)));
      if (stoneType.trim()) formData.append("stone_type", stoneType.trim());
      if (colour.trim()) formData.append("colour", colour.trim());
      if (occasion.trim()) formData.append("occasion", occasion.trim());
      if (productCode.trim()) formData.append("product_code", productCode.trim());
      if (description.trim()) formData.append("description", description.trim());

      const created = await createProduct(formData);
      setSuccess(`Piece "${created.name}" added and indexed in AI visual search!`);

      if (onProductAdded) {
        onProductAdded(created);
      }

      setTimeout(() => {
        // Reset form
        setImageFile(null);
        setImagePreview(null);
        setName("");
        setPrice("");
        setDescription("");
        setProductCode("");
        setSuccess(null);
        onClose();
      }, 1200);
    } catch (err: any) {
      setError(err?.message || "Failed to add jewellery item. Please check image format and details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-ivory border border-gold/40 shadow-2xl p-6 lg:p-8">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full p-2 text-charcoal/60 hover:bg-beige hover:text-ink transition"
          aria-label="Close modal"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Modal Title */}
        <div className="mb-6">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gold/10 text-gold-deep">
              <Plus className="h-5 w-5" />
            </span>
            <h2 className="font-display text-2xl font-light text-ink">Add New Jewellery Item</h2>
          </div>
          <p className="mt-1 text-xs text-charcoal/70">
            Upload piece image and details. OpenCLIP will automatically extract visual features for AI similarity search.
          </p>
        </div>

        {error && (
          <div className="mb-4 flex items-center gap-2 rounded-xl bg-red-50 p-3.5 border border-red-200 text-red-700 text-xs font-medium">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-4 flex items-center gap-2 rounded-xl bg-emerald-50 p-3.5 border border-emerald-200 text-emerald-800 text-xs font-medium">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            <span>{success}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Photo Upload Zone */}
          <div>
            <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase mb-1.5">
              Jewellery Photo <span className="text-gold-deep">*</span>
            </label>
            <div className="relative border-2 border-dashed border-gold/40 rounded-xl bg-white/70 p-4 text-center hover:border-gold transition">
              {imagePreview ? (
                <div className="relative mx-auto h-44 w-44 overflow-hidden rounded-lg border border-line shadow-sm">
                  <img src={imagePreview} alt="Preview" className="h-full w-full object-cover" />
                  <button
                    type="button"
                    onClick={() => {
                      setImageFile(null);
                      setImagePreview(null);
                    }}
                    className="absolute right-2 top-2 rounded-full bg-black/70 p-1 text-white hover:bg-black"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <label className="cursor-pointer flex flex-col items-center justify-center py-6">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gold/10 text-gold-deep mb-2">
                    <Upload className="h-6 w-6" />
                  </div>
                  <span className="text-xs font-semibold text-ink">Click to upload jewellery image</span>
                  <span className="mt-1 text-[11px] text-charcoal/60">Supports JPG, PNG or WebP up to 5MB</span>
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleImageChange}
                    className="hidden"
                  />
                </label>
              )}
            </div>
          </div>

          {/* Form Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase mb-1">
                Product Name <span className="text-gold-deep">*</span>
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Royal Solitaire Diamond Ring"
                className="w-full rounded-xl border border-line bg-white px-3.5 py-2 text-sm text-ink focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase mb-1">
                Price (USD $) <span className="text-gold-deep">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="e.g. 1450.00"
                className="w-full rounded-xl border border-line bg-white px-3.5 py-2 text-sm text-ink focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase mb-1">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-xl border border-line bg-white px-3.5 py-2 text-sm text-ink focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              >
                <option value="Rings">Rings</option>
                <option value="Necklaces">Necklaces</option>
                <option value="Earrings">Earrings</option>
                <option value="Bracelets">Bracelets</option>
                <option value="Pendants">Pendants</option>
                <option value="Bangles">Bangles</option>
                <option value="Anklets">Anklets</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase mb-1">Material</label>
              <select
                value={material}
                onChange={(e) => setMaterial(e.target.value)}
                className="w-full rounded-xl border border-line bg-white px-3.5 py-2 text-sm text-ink focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              >
                <option value="Gold">Gold</option>
                <option value="Diamond">Diamond</option>
                <option value="Platinum">Platinum</option>
                <option value="Silver">Silver</option>
                <option value="Rose Gold">Rose Gold</option>
                <option value="White Gold">White Gold</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase mb-1">Purity</label>
              <input
                type="text"
                value={purity}
                onChange={(e) => setPurity(e.target.value)}
                placeholder="e.g. 22K Gold, 18K Gold, VVS1"
                className="w-full rounded-xl border border-line bg-white px-3.5 py-2 text-sm text-ink focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase mb-1">Weight (grams)</label>
              <input
                type="number"
                step="0.01"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                placeholder="e.g. 14.5"
                className="w-full rounded-xl border border-line bg-white px-3.5 py-2 text-sm text-ink focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase mb-1">Stone Type</label>
              <input
                type="text"
                value={stoneType}
                onChange={(e) => setStoneType(e.target.value)}
                placeholder="e.g. Diamond, Emerald, Ruby, None"
                className="w-full rounded-xl border border-line bg-white px-3.5 py-2 text-sm text-ink focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase mb-1">Occasion</label>
              <select
                value={occasion}
                onChange={(e) => setOccasion(e.target.value)}
                className="w-full rounded-xl border border-line bg-white px-3.5 py-2 text-sm text-ink focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
              >
                <option value="Wedding">Wedding</option>
                <option value="Bridal">Bridal</option>
                <option value="Engagement">Engagement</option>
                <option value="Festive">Festive</option>
                <option value="Party">Party</option>
                <option value="Casual">Casual</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase mb-1">Product Code (Optional)</label>
            <input
              type="text"
              value={productCode}
              onChange={(e) => setProductCode(e.target.value)}
              placeholder="e.g. RG-SOL-990 (Leave blank for auto-generation)"
              className="w-full rounded-xl border border-line bg-white px-3.5 py-2 text-sm text-ink focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase mb-1">Description</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Craftsmanship details, gemstone clarity, cut, design story..."
              className="w-full rounded-xl border border-line bg-white px-3.5 py-2 text-sm text-ink focus:border-gold focus:outline-none focus:ring-1 focus:ring-gold resize-none"
            />
          </div>

          <div className="pt-2 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-line px-5 py-2.5 text-xs font-semibold text-charcoal hover:bg-beige transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-xl bg-ink px-6 py-2.5 text-xs font-semibold text-gold hover:bg-black transition shadow-md disabled:opacity-50"
            >
              {loading ? "Adding & Indexing AI..." : "Add to Catalogue"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
