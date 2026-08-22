import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { logout } from "../services/api.js";
import {
  LayoutDashboard,
  ArrowLeftRight,
  History,
  Shield,
  UserCircle,
  LogOut,
  HelpCircle,
  X,
} from "lucide-react";

const userLinks = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/transfer", label: "Transfer Money", icon: ArrowLeftRight },
  { to: "/transactions", label: "Transactions", icon: History },
  { to: "/profile", label: "Security", icon: Shield },
  { to: "/profile", label: "Profile", icon: UserCircle },
];

const adminLinks = [
  { to: "/admin", label: "Dashboard", icon: LayoutDashboard },
  { to: "/admin/users", label: "Users", icon: UserCircle },
  { to: "/admin/security", label: "Security Events", icon: Shield },
];

export default function Sidebar({ onClose }) {
  const { user, logoutUser } = useAuth();
  const navigate = useNavigate();
  const links = user?.role === "admin" ? adminLinks : userLinks;

  const handleLogout = async () => {
    try {
      await logout();
    } catch {}
    logoutUser();
    navigate("/login");
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-700/50">
      {/* Logo */}
      <div className="flex items-center justify-between px-5 h-16 border-b border-gray-100 dark:border-slate-700/50">
        <NavLink to={user?.role === "admin" ? "/admin" : "/dashboard"} className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-navy-800 rounded-lg flex items-center justify-center">
            <svg className="w-[18px] h-[18px] text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <span className="font-bold text-lg text-navy-900 dark:text-white tracking-tight">VaultX</span>
        </NavLink>
        {onClose && (
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 text-gray-400 dark:text-slate-500 lg:hidden">
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Admin badge */}
      {user?.role === "admin" && (
        <div className="mx-4 mt-4 px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200/60 dark:border-red-800/40 rounded-lg">
          <span className="text-xs font-semibold text-red-700 dark:text-red-400 uppercase tracking-wider">Admin Panel</span>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {links.map((link) => (
          <NavLink
            key={link.to + link.label}
            to={link.to}
            onClick={onClose}
            className={({ isActive }) =>
              isActive ? "sidebar-link-active" : "sidebar-link-inactive"
            }
          >
            <link.icon className="w-5 h-5 flex-shrink-0" />
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Bottom section */}
      <div className="px-3 pb-4 space-y-1 border-t border-gray-100 dark:border-slate-700/50 pt-4">
        <div className="px-3 py-2 flex items-center gap-3">
          <div className="w-8 h-8 bg-navy-100 dark:bg-slate-700 rounded-full flex items-center justify-center">
            <span className="text-sm font-semibold text-navy-700 dark:text-navy-300">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{user?.first_name} {user?.last_name}</p>
            <p className="text-xs text-gray-500 dark:text-slate-500 truncate">@{user?.username}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="sidebar-link-inactive w-full text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-700 dark:hover:text-red-300"
        >
          <LogOut className="w-5 h-5" />
          <span>Log out</span>
        </button>
      </div>
    </div>
  );
}
