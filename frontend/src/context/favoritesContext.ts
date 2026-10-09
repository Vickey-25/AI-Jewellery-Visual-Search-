import { createContext } from "react";

export interface FavoritesValue {
  ids: number[];
  has: (id: number) => boolean;
  toggle: (id: number) => void;
  remove: (id: number) => void;
}

export const FavoritesContext = createContext<FavoritesValue | null>(null);
