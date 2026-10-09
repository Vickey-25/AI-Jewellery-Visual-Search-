import { useContext } from "react";
import { SearchDraftContext } from "../context/searchDraftContext";

export function useSearchDraft() {
  const ctx = useContext(SearchDraftContext);
  if (!ctx) throw new Error("useSearchDraft must be used inside <SearchDraftProvider>");
  return ctx;
}
