import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { SearchDraftContext } from "./searchDraftContext";

export function SearchDraftProvider({ children }: { children: ReactNode }) {
  const [file, setFile] = useState<File | null>(null);
  const value = useMemo(() => ({ file, setFile }), [file]);
  return <SearchDraftContext.Provider value={value}>{children}</SearchDraftContext.Provider>;
}
