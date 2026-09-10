import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldOff } from 'lucide-react';

/**
 * RoleProtectedRoute — wraps routes that require specific roles.
 *
 * Usage:
 *   <RoleProtectedRoute roles="Admin">
 *     <SettingsPage />
 *   </RoleProtectedRoute>
 *
 *   <RoleProtectedRoute roles={["Admin", "Security Analyst"]}>
 *     <AlertDetailPage />
 *   </RoleProtectedRoute>
 *
 * - If no roles prop is given, any authenticated user can access.
 * - Admin always has access to everything.
 * - Viewer and Security Analyst are checked against the allowed roles.
 */
export default function RoleProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-xs font-mono">Checking permissions...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // Admin always has access
  if (user.role === 'Admin') {
    return children;
  }

  // If no specific roles required, any authenticated user can access
  if (!roles) {
    return children;
  }

  // Check if user's role is in the allowed list
  const allowedRoles = Array.isArray(roles) ? roles : [roles];
  if (allowedRoles.includes(user.role)) {
    return children;
  }

  // Access denied — show forbidden page
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto">
          <ShieldOff className="w-8 h-8 text-red-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-100">Access Denied</h2>
          <p className="text-sm text-slate-400 mt-1">
            Your role ({user.role}) does not have permission to access this page.
          </p>
          <p className="text-xs text-slate-500 mt-2">
            Required role: {allowedRoles.join(' or ')}
          </p>
        </div>
      </div>
    </div>
  );
}
