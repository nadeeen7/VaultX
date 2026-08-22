import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext.jsx";
import Navbar from "./components/Navbar.jsx";
import Sidebar from "./components/Sidebar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

// Pages
import LandingPage from "./pages/LandingPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import TransferPage from "./pages/TransferPage.jsx";
import TransactionsPage from "./pages/TransactionsPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import AdminLoginPage from "./pages/AdminLoginPage.jsx";
import AdminDashboardPage from "./pages/AdminDashboardPage.jsx";
import AdminUsersPage from "./pages/AdminUsersPage.jsx";
import AdminSecurityPage from "./pages/AdminSecurityPage.jsx";

function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  // While auth is being validated against backend, show the login/register form.
  // Do NOT redirect during loading — this prevents the stale-token bug where
  // a cached localStorage entry causes an instant redirect to dashboard
  // before backend validation has a chance to reject the expired token.
  if (loading) return children;

  // Auth validation complete — if truly authenticated, redirect away from public routes
  if (user) {
    return <Navigate to={user.role === "admin" ? "/admin" : "/dashboard"} replace />;
  }

  return children;
}

// Layout for authenticated user pages (sidebar + top bar)
function AuthenticatedLayout({ children }) {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex">
      {/* Desktop sidebar */}
      <div className="hidden lg:block lg:w-64 lg:flex-shrink-0">
        <div className="fixed inset-y-0 left-0 w-64">
          <Sidebar />
        </div>
      </div>
      {/* Main content */}
      <div className="flex-1 min-w-0 flex flex-col">
        <Navbar />
        <main className="flex-1 animate-fade-in">{children}</main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      {/* Public routes — no sidebar */}
      <Route path="/" element={<><Navbar /><LandingPage /></>} />
      <Route path="/login" element={
        <PublicRoute><LoginPage /></PublicRoute>
      } />
      <Route path="/register" element={
        <PublicRoute><RegisterPage /></PublicRoute>
      } />
      <Route path="/admin/login" element={
        <PublicRoute><AdminLoginPage /></PublicRoute>
      } />

      {/* Protected user routes — sidebar layout */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <AuthenticatedLayout><DashboardPage /></AuthenticatedLayout>
        </ProtectedRoute>
      } />
      <Route path="/transfer" element={
        <ProtectedRoute>
          <AuthenticatedLayout><TransferPage /></AuthenticatedLayout>
        </ProtectedRoute>
      } />
      <Route path="/transactions" element={
        <ProtectedRoute>
          <AuthenticatedLayout><TransactionsPage /></AuthenticatedLayout>
        </ProtectedRoute>
      } />
      <Route path="/profile" element={
        <ProtectedRoute>
          <AuthenticatedLayout><ProfilePage /></AuthenticatedLayout>
        </ProtectedRoute>
      } />

      {/* Admin routes — sidebar layout */}
      <Route path="/admin" element={
        <ProtectedRoute adminOnly>
          <AuthenticatedLayout><AdminDashboardPage /></AuthenticatedLayout>
        </ProtectedRoute>
      } />
      <Route path="/admin/users" element={
        <ProtectedRoute adminOnly>
          <AuthenticatedLayout><AdminUsersPage /></AuthenticatedLayout>
        </ProtectedRoute>
      } />
      <Route path="/admin/security" element={
        <ProtectedRoute adminOnly>
          <AuthenticatedLayout><AdminSecurityPage /></AuthenticatedLayout>
        </ProtectedRoute>
      } />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
