import { useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { register, googleLogin } from "../services/api.js";
import { useGoogleSignIn } from "../hooks/useGoogleSignIn.js";
import GoogleSignInButton from "../components/GoogleSignInButton.jsx";
import Alert from "../components/Alert.jsx";
import { Eye, EyeOff, ArrowRight, Shield, Check } from "lucide-react";

export default function RegisterPage() {
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    username: "",
    password: "",
    confirm_password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const { loginUser } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!form.first_name.trim() || !form.last_name.trim()) {
      setError("First name and last name are required");
      return;
    }
    if (!form.email.trim()) {
      setError("Email is required");
      return;
    }
    if (!form.username.trim()) {
      setError("Username is required");
      return;
    }
    if (form.password !== form.confirm_password) {
      setError("Passwords do not match");
      return;
    }
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);
    try {
      const res = await register(form);
      loginUser(res.data.token, res.data.user);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.error || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Google Sign-In callback
  const handleGoogleCredential = useCallback(async (response) => {
    setError("");
    setLoading(true);
    try {
      const res = await googleLogin({ credential: response.credential });
      loginUser(res.data.token, res.data.user);
      navigate("/dashboard");
    } catch (err) {
      const msg = err.response?.data?.error || "Google sign-in failed. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [loginUser, navigate]);

  const { googleSignIn, isLoaded: googleLoaded } = useGoogleSignIn(handleGoogleCredential);

  const passwordValid = form.password.length >= 8;
  const passwordMatch = form.password && form.password === form.confirm_password;

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12 bg-slate-50 dark:bg-slate-900">
      <div className="w-full max-w-md animate-slide-up">
        {/* Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-lg p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-12 h-12 bg-navy-800 rounded-xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Create your account</h1>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-1.5">Start your secure banking experience</p>
          </div>

          {/* Error */}
          {error && <Alert type="error" message={error} onClose={() => setError("")} />}

          {/* Google Sign-In */}
          {googleLoaded && (
            <div className="mt-6">
              <GoogleSignInButton onClick={googleSignIn} loading={loading} />
            </div>
          )}

          {/* Divider */}
          {googleLoaded && (
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200 dark:border-slate-600" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="px-3 bg-white dark:bg-slate-800 text-gray-400 dark:text-slate-500">or register with email</span>
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className={!googleLoaded ? "mt-6 space-y-4" : "space-y-4"}>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">First Name</label>
                <input
                  type="text"
                  name="first_name"
                  value={form.first_name}
                  onChange={handleChange}
                  required
                  placeholder="John"
                  className="input-field"
                />
              </div>
              <div>
                <label className="label">Last Name</label>
                <input
                  type="text"
                  name="last_name"
                  value={form.last_name}
                  onChange={handleChange}
                  required
                  placeholder="Doe"
                  className="input-field"
                />
              </div>
            </div>

            <div>
              <label className="label">Email</label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                required
                placeholder="john@example.com"
                className="input-field"
                autoComplete="email"
              />
            </div>

            <div>
              <label className="label">Username</label>
              <input
                type="text"
                name="username"
                value={form.username}
                onChange={handleChange}
                required
                placeholder="johndoe"
                className="input-field"
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
                  placeholder="Min. 8 characters"
                  className="input-field !pr-11"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {form.password && (
                <div className="flex items-center gap-1.5 mt-1.5">
                  <Check className={`w-3.5 h-3.5 ${passwordValid ? "text-emerald-500" : "text-gray-300 dark:text-slate-600"}`} />
                  <span className={`text-xs ${passwordValid ? "text-emerald-600 dark:text-emerald-400" : "text-gray-400 dark:text-slate-500"}`}>
                    At least 8 characters
                  </span>
                </div>
              )}
            </div>

            <div>
              <label className="label">Confirm Password</label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  name="confirm_password"
                  value={form.confirm_password}
                  onChange={handleChange}
                  required
                  placeholder="Re-enter password"
                  className="input-field !pr-11"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 transition-colors"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {form.confirm_password && (
                <div className="flex items-center gap-1.5 mt-1.5">
                  <Check className={`w-3.5 h-3.5 ${passwordMatch ? "text-emerald-500" : "text-gray-300 dark:text-slate-600"}`} />
                  <span className={`text-xs ${passwordMatch ? "text-emerald-600 dark:text-emerald-400" : "text-gray-400 dark:text-slate-500"}`}>
                    Passwords match
                  </span>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full !py-3 mt-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating account...
                </>
              ) : (
                <>
                  Create Account
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Sign in link */}
          <p className="text-center text-sm text-gray-500 dark:text-slate-400 mt-6">
            Already have an account?{" "}
            <Link to="/login" className="text-accent-600 hover:text-accent-700 dark:text-accent-400 dark:hover:text-accent-300 font-medium">
              Sign in
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
