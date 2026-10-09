import { createContext } from "react";

export interface SearchDraftValue {
  /** The image the customer picked. Files can't live in a URL, so it is held here between pages. */
  file: File | null;
  setFile: (file: File | null) => void;
}

export const SearchDraftContext = createContext<SearchDraftValue | null>(null);
