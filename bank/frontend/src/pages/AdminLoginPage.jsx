import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { adminLogin } from "../services/api.js";
import Alert from "../components/Alert.jsx";
import { Eye, EyeOff, ArrowRight, Shield, Lock } from "lucide-react";

export default function AdminLoginPage() {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { loginUser } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await adminLogin(form);
      loginUser(res.data.token, res.data.user);
      navigate("/admin");
    } catch (err) {
      setError(err.response?.data?.error || "Admin login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12 bg-slate-50 dark:bg-slate-900">
      <div className="w-full max-w-md animate-slide-up">
        {/* Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-lg p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-12 h-12 bg-red-50 dark:bg-red-900/20 rounded-xl flex items-center justify-center mx-auto mb-4 border border-red-200/60 dark:border-red-800/40">
              <Shield className="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
            <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Admin Access</h1>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1.5">Restricted — authorized personnel only</p>
          </div>

          {/* Error */}
          {error && <Alert type="error" message={error} onClose={() => setError("")} />}

          {/* Form */}
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="label">Admin Username</label>
              <input
                type="text"
                name="username"
                value={form.username}
                onChange={handleChange}
                required
                className="input-field"
                placeholder="Enter admin username"
                autoComplete="username"
              />
            </div>
            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={form.password}
                  onChange={handleChange}
                  required
                  className="input-field !pr-11"
                  placeholder="Enter password"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full !py-3 !bg-red-600 hover:!bg-red-700"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Authenticating...
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4" />
                  Admin Sign In
                </>
              )}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 dark:text-slate-400 mt-6">
            <Link to="/login" className="text-accent-600 hover:text-accent-700 dark:text-accent-400 dark:hover:text-accent-300 font-medium">
              ← Back to User Login
            </Link>
          </p>
        </div>

        {/* Security badge */}
        <div className="flex items-center justify-center gap-2 mt-6 text-gray-400 dark:text-slate-500">
          <Shield className="w-3.5 h-3.5" />
          <span className="text-xs font-medium">Encrypted • Admin-only access</span>
        </div>
      </div>
    </div>
  );
}
