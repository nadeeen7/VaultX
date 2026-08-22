import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useTheme } from "../context/ThemeContext.jsx";
import { logout } from "../services/api.js";
import { Menu, Bell, Search, ChevronDown, Sun, Moon } from "lucide-react";
import Sidebar from "./Sidebar.jsx";

export default function Navbar() {
  const { user, logoutUser } = useAuth();
  const { dark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // Backend may be unavailable - still clear local auth state
    }
    // Always clear local auth state regardless of backend response
    logoutUser();
    // Use replace so the user cannot navigate back to authenticated pages
    navigate("/login", { replace: true });
  };

  // Landing page / public pages navbar
  if (!user) {
    return (
      <nav className="sticky top-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-gray-200 dark:border-slate-700/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-navy-800 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <span className="font-bold text-lg text-navy-900 dark:text-white tracking-tight">VaultX</span>
          </Link>
          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 dark:text-slate-400 transition-colors"
              aria-label="Toggle theme"
            >
              {dark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <Link
              to="/login"
              className="text-sm font-medium text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="btn-primary !py-2 !px-5 text-sm"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>
    );
  }

  // Authenticated top bar
  return (
    <>
      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-black/30 dark:bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="fixed inset-y-0 left-0 w-72 z-50 animate-slide-in-left">
            <Sidebar onClose={() => setMobileOpen(false)} />
          </div>
        </div>
      )}

      {/* Top bar */}
      <header className="sticky top-0 z-40 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-gray-200 dark:border-slate-700/50 h-16">
        <div className="flex items-center justify-between h-full px-4 lg:px-6">
          {/* Left: hamburger + page context */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-500 dark:text-slate-400 lg:hidden"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="hidden lg:flex items-center gap-2">
              <div className="w-7 h-7 bg-navy-800 rounded-md flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <span className="font-bold text-navy-900 dark:text-white tracking-tight">VaultX</span>
            </div>
          </div>

          {/* Right: actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 transition-colors"
              aria-label="Toggle theme"
            >
              {dark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 transition-colors relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
            </button>

            <div className="relative">
              <button
                onClick={() => setProfileOpen(!profileOpen)}
                className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
              >
                <div className="w-8 h-8 bg-navy-100 dark:bg-slate-700 rounded-full flex items-center justify-center">
                  <span className="text-sm font-semibold text-navy-700 dark:text-navy-300">
                    {user?.first_name?.[0]}{user?.last_name?.[0]}
                  </span>
                </div>
                <span className="hidden sm:block text-sm font-medium text-gray-700 dark:text-slate-300">
                  {user?.first_name}
                </span>
                <ChevronDown className="hidden sm:block w-4 h-4 text-gray-400 dark:text-slate-500" />
              </button>

              {profileOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setProfileOpen(false)} />
                  <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 shadow-lg z-50 py-1.5 animate-fade-in">
                    <div className="px-4 py-3 border-b border-gray-100 dark:border-slate-700">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{user?.first_name} {user?.last_name}</p>
                      <p className="text-xs text-gray-500 dark:text-slate-500 mt-0.5">@{user?.username}</p>
                      {user?.role === "admin" && (
                        <span className="inline-block mt-1.5 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-full border border-red-200/60 dark:border-red-800/40">Admin</span>
                      )}
                    </div>
                    <div className="py-1">
                      <Link
                        to="/profile"
                        onClick={() => setProfileOpen(false)}
                        className="flex items-center gap-2.5 px-4 py-2 text-sm text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700"
                      >
                        Profile & Security
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                      >
                        Log out
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>
    </>
  );
}
