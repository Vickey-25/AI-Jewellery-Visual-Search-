import { Crown, Heart, LogOut, MessageSquare, User, X } from "lucide-react";
import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import Modal from "../ui/Modal";
import { NAV_ITEMS } from "./navItems";

interface Props {
  open: boolean;
  onClose: () => void;
  favoritesCount: number;
}

export default function MobileMenu({ open, onClose, favoritesCount }: Props) {
  const { isAuthenticated, user, isOwner, logout } = useAuth();

  return (
    <Modal open={open} onClose={onClose} label="Main menu" placement="right">
      <div className="flex h-full flex-col p-6 overflow-y-auto">
        <div className="flex items-center justify-between border-b border-line pb-4">
          <span className="font-display text-xl tracking-[0.25em]">LUMIÈRE</span>
          <button type="button" onClick={onClose} aria-label="Close menu" className="rounded-lg p-2 hover:bg-beige">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* User Role Card in Mobile Menu */}
        {isAuthenticated && user && (
          <div className="mt-4 rounded-xl bg-beige/60 p-4 border border-gold/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              {isOwner ? <Crown className="h-5 w-5 text-gold-deep" /> : <User className="h-5 w-5 text-charcoal/70" />}
              <div>
                <p className="text-sm font-semibold text-ink leading-tight">{user.full_name}</p>
                <p className="text-[10px] font-bold text-gold-deep uppercase tracking-wider">
                  {isOwner ? "Shop Owner" : "Customer Portal"}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                logout();
                onClose();
              }}
              className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}

        <nav aria-label="Mobile" className="mt-6 flex flex-col">
          {NAV_ITEMS.map((item) =>
            item.hash ? (
              <Link key={item.label} to={item.to} onClick={onClose} className="border-b border-line py-3.5 font-display text-xl">
                {item.label}
              </Link>
            ) : (
              <NavLink
                key={item.label}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  `border-b border-line py-3.5 font-display text-xl ${isActive ? "text-gold-deep" : ""}`
                }
              >
                {item.label}
              </NavLink>
            ),
          )}

          {/* Enquiries Link */}
          {isAuthenticated ? (
            <NavLink
              to={isOwner ? "/owner/enquiries" : "/my-enquiries"}
              onClick={onClose}
              className={({ isActive }) =>
                `border-b border-line py-3.5 font-display text-xl flex items-center gap-2 ${
                  isActive ? "text-gold-deep" : ""
                }`
              }
            >
              <MessageSquare className="h-5 w-5 text-gold-deep" />
              <span>{isOwner ? "Owner Enquiries" : "My Enquiries"}</span>
            </NavLink>
          ) : (
            <Link
              to="/login"
              onClick={onClose}
              className="mt-4 flex items-center justify-center gap-2 rounded-xl bg-gold py-3 font-semibold text-dark text-sm shadow-sm"
            >
              <User className="h-4 w-4" />
              <span>Sign In / Register</span>
            </Link>
          )}
        </nav>

        <Link to="/favorites" onClick={onClose} className="mt-6 flex items-center gap-3 py-3 text-ink font-medium">
          <Heart className="h-5 w-5 text-gold-deep" strokeWidth={1.6} />
          Favorites{favoritesCount > 0 ? ` (${favoritesCount})` : ""}
        </Link>

        <p className="mt-auto pt-8 text-xs tracking-[0.3em] text-muted">AI JEWELLERY VISUAL SEARCH</p>
      </div>
    </Modal>
  );
}
