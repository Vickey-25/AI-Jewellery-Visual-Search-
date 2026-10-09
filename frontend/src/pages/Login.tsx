import { AlertCircle, CheckCircle2, Crown, Lock, Mail, Phone, User as UserIcon, UserCheck } from "lucide-react";
import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { loginApi, registerApi } from "../api/authApi";
import { useAuth } from "../hooks/useAuth";
import type { UserRole } from "../types/auth";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, user, logout } = useAuth();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [selectedRole, setSelectedRole] = useState<UserRole>("customer");

  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || "/";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      if (mode === "login") {
        const res = await loginApi({
          email: email.trim(),
          password,
          role: selectedRole,
        });
        login(res.token, res.user);
        setSuccess(`Welcome back, ${res.user.full_name}!`);
        setTimeout(() => {
          if (res.user.role === "shopowner") {
            navigate("/owner/enquiries");
          } else {
            navigate(from);
          }
        }, 800);
      } else {
        const res = await registerApi({
          email: email.trim(),
          password,
          full_name: fullName.trim(),
          role: selectedRole,
          phone: phone.trim() || undefined,
        });
        login(res.token, res.user);
        setSuccess(`Account created successfully! Welcome to Lumière, ${res.user.full_name}.`);
        setTimeout(() => {
          if (res.user.role === "shopowner") {
            navigate("/owner/enquiries");
          } else {
            navigate(from);
          }
        }, 800);
      }
    } catch (err: any) {
      setError(err?.message || "An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoLogin = async (role: UserRole) => {
    setError(null);
    setSuccess(null);
    setLoading(true);
    setSelectedRole(role);

    const demoEmail = role === "shopowner" ? "owner@lumiere.com" : "customer@lumiere.com";
    const demoPass = "password123";
    setEmail(demoEmail);
    setPassword(demoPass);

    try {
      // First attempt login
      let res;
      try {
        res = await loginApi({ email: demoEmail, password: demoPass, role });
      } catch {
        // If demo user doesn't exist, auto-register demo user
        res = await registerApi({
          email: demoEmail,
          password: demoPass,
          full_name: role === "shopowner" ? "Elena Rostova (Store Owner)" : "Sophia Vance (Client)",
          role,
          phone: "+1 555 019 2834",
        });
      }
      login(res.token, res.user);
      setSuccess(`Signed in as Demo ${role === "shopowner" ? "Shop Owner" : "Customer"}`);
      setTimeout(() => {
        if (role === "shopowner") {
          navigate("/owner/enquiries");
        } else {
          navigate("/");
        }
      }, 700);
    } catch (err: any) {
      setError(err?.message || "Could not log into demo account.");
    } finally {
      setLoading(false);
    }
  };

  if (isAuthenticated && user) {
    return (
      <div className="container-page py-16">
        <div className="mx-auto max-w-md rounded-2xl border border-gold/30 bg-white/80 p-8 text-center shadow-lg backdrop-blur-md">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gold/10 text-gold-deep">
            {user.role === "shopowner" ? <Crown className="h-7 w-7" /> : <UserCheck className="h-7 w-7" />}
          </div>
          <h2 className="mt-4 font-display text-2xl text-ink">Already Signed In</h2>
          <p className="mt-2 text-sm text-charcoal/70">
            You are logged in as <strong className="text-ink">{user.full_name}</strong> ({user.role === "shopowner" ? "Shop Owner" : "Customer"}).
          </p>
          <div className="mt-6 flex flex-col gap-3">
            {user.role === "shopowner" && (
              <button
                type="button"
                onClick={() => navigate("/owner/enquiries")}
                className="w-full rounded-xl bg-ink py-3 text-sm font-medium text-gold hover:bg-black"
              >
                Go to Owner Dashboard & Enquiries
              </button>
            )}
            <button
              type="button"
              onClick={() => navigate("/products")}
              className="w-full rounded-xl border border-line py-3 text-sm font-medium text-ink hover:bg-beige/50"
            >
              Explore Catalogue
            </button>
            <button
              type="button"
              onClick={logout}
              className="w-full rounded-xl bg-red-50 py-2.5 text-xs font-semibold text-red-600 hover:bg-red-100"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container-page py-12 lg:py-16">
      <div className="mx-auto max-w-lg">
        {/* Header Title */}
        <div className="text-center">
          <span className="text-xs font-semibold tracking-[0.3em] uppercase text-gold-deep">Lumière Luxury Portal</span>
          <h1 className="mt-2 font-display text-3xl font-light text-ink lg:text-4xl">
            {mode === "login" ? "Access Your Account" : "Create Nouveau Account"}
          </h1>
          <p className="mt-2 text-sm text-charcoal/70">
            Select your portal role to experience personalized visual search and inventory management.
          </p>
        </div>

        {/* Role Switcher Tabs */}
        <div className="mt-8 grid grid-cols-2 gap-3 rounded-xl bg-beige/60 p-1.5 border border-gold/20">
          <button
            type="button"
            onClick={() => setSelectedRole("customer")}
            className={`flex items-center justify-center gap-2 rounded-lg py-3 text-sm font-medium transition-all ${
              selectedRole === "customer"
                ? "bg-white text-ink shadow-sm font-semibold"
                : "text-charcoal/70 hover:text-ink"
            }`}
          >
            <UserIcon className={`h-4 w-4 ${selectedRole === "customer" ? "text-gold-deep" : ""}`} />
            <span>Customer Portal</span>
          </button>

          <button
            type="button"
            onClick={() => setSelectedRole("shopowner")}
            className={`flex items-center justify-center gap-2 rounded-lg py-3 text-sm font-medium transition-all ${
              selectedRole === "shopowner"
                ? "bg-ink text-gold shadow-sm font-semibold"
                : "text-charcoal/70 hover:text-ink"
            }`}
          >
            <Crown className={`h-4 w-4 ${selectedRole === "shopowner" ? "text-gold" : ""}`} />
            <span>Shop Owner</span>
          </button>
        </div>

        {/* Form Container */}
        <div className="mt-6 rounded-2xl border border-line bg-white/90 p-8 shadow-soft backdrop-blur-md">
          {error && (
            <div className="mb-6 flex items-start gap-3 rounded-xl bg-red-50 p-4 border border-red-200/60 text-red-700 text-sm">
              <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-6 flex items-start gap-3 rounded-xl bg-emerald-50 p-4 border border-emerald-200/60 text-emerald-800 text-sm">
              <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "register" && (
              <div>
                <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase">Full Name</label>
                <div className="mt-1.5 relative">
                  <UserIcon className="absolute left-3.5 top-3 h-4 w-4 text-charcoal/40" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Eleanor Vance"
                    className="w-full rounded-xl border border-line bg-beige/30 pl-10 pr-4 py-2.5 text-sm text-ink placeholder:text-charcoal/40 focus:border-gold focus:bg-white focus:outline-none focus:ring-1 focus:ring-gold"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase">Email Address</label>
              <div className="mt-1.5 relative">
                <Mail className="absolute left-3.5 top-3 h-4 w-4 text-charcoal/40" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={selectedRole === "shopowner" ? "owner@lumiere.com" : "customer@lumiere.com"}
                  className="w-full rounded-xl border border-line bg-beige/30 pl-10 pr-4 py-2.5 text-sm text-ink placeholder:text-charcoal/40 focus:border-gold focus:bg-white focus:outline-none focus:ring-1 focus:ring-gold"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase">Password</label>
              <div className="mt-1.5 relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-charcoal/40" />
                <input
                  type="password"
                  required
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-line bg-beige/30 pl-10 pr-4 py-2.5 text-sm text-ink placeholder:text-charcoal/40 focus:border-gold focus:bg-white focus:outline-none focus:ring-1 focus:ring-gold"
                />
              </div>
            </div>

            {mode === "register" && (
              <div>
                <label className="block text-xs font-semibold tracking-wider text-charcoal uppercase">Phone Number (Optional)</label>
                <div className="mt-1.5 relative">
                  <Phone className="absolute left-3.5 top-3 h-4 w-4 text-charcoal/40" />
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+1 (555) 000-0000"
                    className="w-full rounded-xl border border-line bg-beige/30 pl-10 pr-4 py-2.5 text-sm text-ink placeholder:text-charcoal/40 focus:border-gold focus:bg-white focus:outline-none focus:ring-1 focus:ring-gold"
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className={`w-full mt-2 rounded-xl py-3.5 text-sm font-semibold transition-all ${
                selectedRole === "shopowner"
                  ? "bg-ink text-gold hover:bg-black shadow-md"
                  : "bg-gold text-dark hover:bg-gold-deep shadow-md"
              } disabled:opacity-50`}
            >
              {loading
                ? "Processing..."
                : mode === "login"
                ? `Sign In as ${selectedRole === "shopowner" ? "Shop Owner" : "Customer"}`
                : `Create ${selectedRole === "shopowner" ? "Shop Owner" : "Customer"} Account`}
            </button>
          </form>

          {/* Switch Mode Toggle */}
          <div className="mt-6 text-center text-sm text-charcoal/70">
            {mode === "login" ? (
              <p>
                Don't have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setMode("register");
                    setError(null);
                  }}
                  className="font-semibold text-gold-deep underline decoration-gold/50 hover:text-ink"
                >
                  Create one now
                </button>
              </p>
            ) : (
              <p>
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setMode("login");
                    setError(null);
                  }}
                  className="font-semibold text-gold-deep underline decoration-gold/50 hover:text-ink"
                >
                  Sign in
                </button>
              </p>
            )}
          </div>

          {/* Quick Demo Login Bar */}
          <div className="mt-8 border-t border-line/80 pt-6">
            <span className="block text-center text-xs font-semibold tracking-wider text-charcoal/60 uppercase">
              ⚡ Quick Demo One-Click Login
            </span>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => handleQuickDemoLogin("customer")}
                disabled={loading}
                className="flex items-center justify-center gap-1.5 rounded-lg border border-line bg-beige/40 py-2.5 text-xs font-medium text-ink hover:bg-gold/10"
              >
                <UserIcon className="h-3.5 w-3.5 text-gold-deep" />
                <span>Demo Customer</span>
              </button>
              <button
                type="button"
                onClick={() => handleQuickDemoLogin("shopowner")}
                disabled={loading}
                className="flex items-center justify-center gap-1.5 rounded-lg border border-gold/40 bg-ink py-2.5 text-xs font-medium text-gold hover:bg-black"
              >
                <Crown className="h-3.5 w-3.5 text-gold" />
                <span>Demo Owner</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
