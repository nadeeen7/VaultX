import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth();

  // CRITICAL: While auth state is being determined, show spinner.
  // NEVER redirect during loading — this prevents race conditions
  // where stale localStorage data causes an unauthorized dashboard flash.
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-900">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-[3px] border-gray-200 dark:border-slate-700 border-t-navy-800 dark:border-t-navy-400 rounded-full animate-spin" />
          <p className="text-sm text-gray-500 dark:text-slate-400 font-medium">Verifying authentication...</p>
        </div>
      </div>
    );
  }

  // Auth validation complete — no user means unauthenticated
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && user.role !== "admin") return <Navigate to="/dashboard" replace />;

  return children;
}
