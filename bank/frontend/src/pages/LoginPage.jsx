import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { login } from "../services/api.js";
import Alert from "../components/Alert.jsx";
import { Eye, EyeOff, ArrowRight, Shield } from "lucide-react";

export default function LoginPage() {
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
    setError("");

    // Explicit client-side validation — never attempt API call with empty fields
    if (!form.username.trim()) {
      setError("Please enter your username or email");
      return;
    }
    if (!form.password) {
      setError("Please enter your password");
      return;
    }

    setLoading(true);

    try {
      // ONLY navigate after backend confirms authentication
      const res = await login(form);
      loginUser(res.data.token, res.data.user);

      if (res.data.user.role === "admin") {
        navigate("/admin");
      } else {
        navigate("/dashboard");
      }
    } catch (err) {
      const msg = err.response?.data?.error || "Login failed. Please try again.";
      setError(msg);
      // DO NOT navigate on failure
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
            <div className="w-12 h-12 bg-navy-800 rounded-xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Welcome back</h1>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1.5">Sign in to your VaultX account</p>
          </div>

          {/* Error */}
          {error && <Alert type="error" message={error} onClose={() => setError("")} />}

          {/* Form */}
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="label">Username or Email</label>
              <input
                type="text"
                name="username"
                value={form.username}
                onChange={handleChange}
                required
                className="input-field"
                placeholder="Enter your username"
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
                  placeholder="Enter your password"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full !py-3 mt-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Register link */}
          <p className="text-center text-sm text-gray-500 dark:text-slate-400 mt-6">
            Don&apos;t have an account?{" "}
            <Link to="/register" className="text-accent-600 hover:text-accent-700 dark:text-accent-400 dark:hover:text-accent-300 font-medium">
              Create account
            </Link>
          </p>
        </div>

        {/* Security badge */}
        <div className="flex items-center justify-center gap-2 mt-6 text-gray-400 dark:text-slate-500">
          <Shield className="w-3.5 h-3.5" />
          <span className="text-xs font-medium">256-bit encrypted • Secure banking</span>
        </div>
      </div>
    </div>
  );
}
