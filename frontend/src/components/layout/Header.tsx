import { Crown, Heart, LogOut, Menu, MessageSquare, Plus, Search, User } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import AddProductModal from "../products/AddProductModal";
import { useAuth } from "../../hooks/useAuth";
import { useFavorites } from "../../hooks/useFavorites";
import MobileMenu from "./MobileMenu";
import { NAV_ITEMS } from "./navItems";
import SearchOverlay from "./SearchOverlay";

const linkBase = "relative py-1 text-sm tracking-wide transition-colors hover:text-gold-deep";
const iconButton = "relative rounded-lg p-2.5 text-ink transition hover:bg-beige";

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const { ids } = useFavorites();
  const { isAuthenticated, user, isOwner, logout } = useAuth();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-40 border-b transition-all duration-300 ${
        scrolled ? "border-line bg-ivory/90 shadow-soft backdrop-blur-md" : "border-transparent bg-ivory/60 backdrop-blur-sm"
      }`}
    >
      <div className="container-page flex h-[72px] items-center justify-between">
        <Link to="/" className="flex flex-col leading-none" aria-label="Lumière AI Jewellery, home">
          <span className="font-display text-[22px] tracking-[0.28em] text-ink">LUMIÈRE</span>
          <span className="mt-1.5 text-[9px] font-medium tracking-[0.42em] text-gold-deep">AI JEWELLERY</span>
        </Link>

        <nav aria-label="Main" className="hidden items-center gap-8 lg:flex">
          {NAV_ITEMS.map((item) =>
            item.hash ? (
              <Link key={item.label} to={item.to} className={linkBase}>
                {item.label}
              </Link>
            ) : (
              <NavLink
                key={item.label}
                to={item.to}
                className={({ isActive }) =>
                  `${linkBase} ${isActive ? "text-gold-deep after:absolute after:inset-x-0 after:-bottom-0.5 after:h-px after:bg-gold" : ""}`
                }
              >
                {item.label}
              </NavLink>
            ),
          )}

          {/* Role Based Navigation Links */}
          {isAuthenticated && (
            <NavLink
              to={isOwner ? "/owner/enquiries" : "/my-enquiries"}
              className={({ isActive }) =>
                `${linkBase} flex items-center gap-1.5 ${
                  isActive ? "text-gold-deep after:absolute after:inset-x-0 after:-bottom-0.5 after:h-px after:bg-gold" : ""
                }`
              }
            >
              <MessageSquare className="h-4 w-4 text-gold-deep" />
              <span>{isOwner ? "Enquiries Portal" : "My Enquiries"}</span>
            </NavLink>
          )}
        </nav>

        <div className="flex items-center gap-2">
          {/* Owner Quick Add Button */}
          {isOwner && (
            <button
              type="button"
              onClick={() => setAddModalOpen(true)}
              className="hidden sm:flex items-center gap-1.5 rounded-lg bg-ink px-3 py-1.5 text-xs font-semibold text-gold hover:bg-black transition shadow-xs"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add Item</span>
            </button>
          )}

          <button type="button" className={`${iconButton} hidden lg:block`} onClick={() => setSearchOpen(true)} aria-label="Search jewellery">
            <Search className="h-5 w-5" strokeWidth={1.6} />
          </button>
          <Link to="/favorites" className={iconButton} aria-label={`Favorites${ids.length ? `, ${ids.length} saved` : ""}`}>
            <Heart className="h-5 w-5" strokeWidth={1.6} />
            {ids.length > 0 && (
              <span className="absolute right-0.5 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-gold px-1 text-[10px] font-semibold text-dark">
                {ids.length}
              </span>
            )}
          </Link>

          {/* User Auth Info & Actions */}
          {isAuthenticated && user ? (
            <div className="hidden lg:flex items-center gap-2 pl-2 border-l border-line">
              <div className="flex items-center gap-2 rounded-full bg-beige/80 px-3 py-1 border border-gold/30">
                {isOwner ? (
                  <Crown className="h-3.5 w-3.5 text-gold-deep" />
                ) : (
                  <User className="h-3.5 w-3.5 text-charcoal/70" />
                )}
                <span className="text-xs font-semibold text-ink max-w-[110px] truncate">{user.full_name}</span>
                <span className="text-[10px] font-bold tracking-wider uppercase text-gold-deep px-1.5 py-0.2 rounded bg-gold/15">
                  {isOwner ? "Owner" : "Customer"}
                </span>
              </div>
              <button
                type="button"
                onClick={logout}
                className="p-2 text-charcoal/60 hover:text-red-600 transition"
                title="Sign Out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="hidden lg:flex items-center gap-1.5 rounded-lg border border-gold/40 bg-gold/10 px-3.5 py-1.5 text-xs font-semibold text-ink hover:bg-gold hover:text-dark transition"
            >
              <User className="h-3.5 w-3.5 text-gold-deep" />
              <span>Sign In</span>
            </Link>
          )}

          <button type="button" className={`${iconButton} lg:hidden`} onClick={() => setSearchOpen(true)} aria-label="Search jewellery">
            <Search className="h-5 w-5" strokeWidth={1.6} />
          </button>
          <button
            type="button"
            className={`${iconButton} lg:hidden`}
            onClick={() => setMenuOpen(true)}
            aria-label="Open menu"
            aria-haspopup="dialog"
          >
            <Menu className="h-5 w-5" strokeWidth={1.6} />
          </button>
        </div>
      </div>

      <MobileMenu open={menuOpen} onClose={() => setMenuOpen(false)} favoritesCount={ids.length} />
      <SearchOverlay open={searchOpen} onClose={() => setSearchOpen(false)} />
      <AddProductModal open={addModalOpen} onClose={() => setAddModalOpen(false)} />
    </header>
  );
}
