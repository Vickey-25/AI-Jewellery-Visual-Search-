import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, DragEvent, KeyboardEvent } from "react";
import { formatBytes } from "../format";

const MAX_BYTES = 5 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const ALLOWED_EXT = /\.(jpe?g|png|webp)$/i;

interface Props {
  loading: boolean;
  onSearch: (file: File) => void;
  serverError?: string | null;
}

function validate(file: File): string | null {
  const typeOk = ALLOWED_TYPES.includes(file.type) || (file.type === "" && ALLOWED_EXT.test(file.name));
  if (!typeOk) return "Unsupported format. Please use a JPG, PNG or WebP image.";
  if (file.size > MAX_BYTES) return "Image is too large. Maximum size is 5 MB.";
  if (file.size === 0) return "Please upload a valid jewellery image.";
  return null;
}

export default function ImageUploader({ loading, onSearch, serverError }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function accept(candidate: File | undefined) {
    if (!candidate) return;
    const problem = validate(candidate);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setFile(candidate);
  }

  function onPick(e: ChangeEvent<HTMLInputElement>) {
    accept(e.target.files?.[0]);
    e.target.value = ""; // allow picking the same file again after removing it
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    if (!loading) accept(e.dataTransfer.files?.[0]);
  }

  function onZoneKey(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      inputRef.current?.click();
    }
  }

  function remove() {
    setFile(null);
    setError(null);
  }

  function submit() {
    if (!file) {
      setError("Please select a jewellery image first.");
      return;
    }
    setError(null);
    onSearch(file);
  }

  const message = error ?? serverError ?? null;

  return (
    <section className="tray" aria-label="Upload a jewellery image">
      <input
        ref={inputRef}
        type="file"
        className="visually-hidden"
        accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
        onChange={onPick}
        tabIndex={-1}
      />

      {file && preview ? (
        <div className="tray-preview">
          <img src={preview} alt="Your uploaded jewellery" className="tray-image" />
          <div className="tray-side">
            <p className="tray-filename">{file.name}</p>
            <p className="tray-filesize">{formatBytes(file.size)}</p>
            <div className="tray-actions">
              <button type="button" className="btn btn-primary" onClick={submit} disabled={loading}>
                {loading ? "Searching..." : "Search Similar Jewellery"}
              </button>
              <button type="button" className="btn btn-ghost" onClick={remove} disabled={loading}>
                Remove
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div
          className={`dropzone${dragging ? " is-dragging" : ""}`}
          role="button"
          tabIndex={0}
          aria-label="Choose a jewellery image or drop one here"
          onClick={() => inputRef.current?.click()}
          onKeyDown={onZoneKey}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <svg className="gem-icon" viewBox="0 0 64 56" aria-hidden="true">
            <path d="M16 4h32l14 16-30 32L2 20z" />
            <path d="M2 20h60M22 20l10 32 10-32M16 4l6 16 10-16 10 16 6-16" />
          </svg>
          <p className="dropzone-title">Drag and drop a jewellery image here</p>
          <p className="dropzone-sub">or</p>
          <span className="btn btn-primary">Upload Image</span>
          <p className="dropzone-hint">JPG, PNG or WebP, up to 5 MB</p>
        </div>
      )}

      {message && (
        <p className="tray-error" role="alert">
          {message}
        </p>
      )}
    </section>
  );
}
