interface Props {
  title?: string;
  detail?: string;
}

export default function Loading({
  title = "Analyzing your jewellery image...",
  detail = "Finding visually similar jewellery...",
}: Props) {
  return (
    <div className="loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <div>
        <p className="loading-title">{title}</p>
        <p className="loading-detail">{detail}</p>
      </div>
    </div>
  );
}
