export interface NavItem {
  label: string;
  to: string;
  /** Hash links scroll within the home page, so they are not "active" routes. */
  hash?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Discover", to: "/products" },
  { label: "Visual Search", to: "/search" },
  { label: "Collections", to: "/#collections", hash: true },
  { label: "About", to: "/about" },
];
