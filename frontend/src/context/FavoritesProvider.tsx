import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { FavoritesContext } from "./favoritesContext";

const STORAGE_KEY = "lumiere:favorites";

function read(): number[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((n): n is number => Number.isInteger(n)) : [];
  } catch {
    return [];
  }
}

/** Wishlist kept in localStorage (no account needed). Stores product ids only. */
export function FavoritesProvider({ children }: { children: ReactNode }) {
  const [ids, setIds] = useState<number[]>(read);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
    } catch {
      // storage can be unavailable (private mode); the wishlist then lasts for this session only
    }
  }, [ids]);

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) setIds(read());
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const toggle = useCallback(
    (id: number) => setIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [id, ...prev])),
    [],
  );
  const remove = useCallback((id: number) => setIds((prev) => prev.filter((x) => x !== id)), []);

  const value = useMemo(() => ({ ids, has: (id: number) => ids.includes(id), toggle, remove }), [ids, toggle, remove]);
  return <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>;
}
