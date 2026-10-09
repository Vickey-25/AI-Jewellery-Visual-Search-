import { ButtonLink } from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";

export default function NotFound() {
  return (
    <EmptyState title="This page has wandered off" description="The page you're looking for doesn't exist.">
      <ButtonLink to="/" variant="primary">Back to home</ButtonLink>
      <ButtonLink to="/products" variant="outline">Explore Collection</ButtonLink>
    </EmptyState>
  );
}
