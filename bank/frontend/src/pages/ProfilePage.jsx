import { useState, useEffect } from "react";
import { getProfile, changePassword, getLoginHistory } from "../services/api.js";
import { useAuth } from "../context/AuthContext.jsx";
import LoadingSpinner from "../components/LoadingSpinner.jsx";
import Alert from "../components/Alert.jsx";
import {
  User,
  Shield,
  Lock,
  Key,
  Clock,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  CreditCard,
} from "lucide-react";

export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loginHistory, setLoginHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [pwLoading, setPwLoading] = useState(false);
  const [pwMessage, setPwMessage] = useState({ type: "", text: "" });
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [profRes, histRes] = await Promise.all([
          getProfile(),
          getLoginHistory({ per_page: 10 }),
        ]);
        setProfile(profRes.data);
        setLoginHistory(histRes.data.login_history);
      } catch (err) {
        console.error("Failed to load profile", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPwMessage({ type: "", text: "" });

    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPwMessage({ type: "error", text: "New passwords do not match" });
      return;
    }
    if (passwordForm.new_password.length < 8) {
      setPwMessage({ type: "error", text: "New password must be at least 8 characters" });
      return;
    }

    setPwLoading(true);
    try {
      await changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      setPwMessage({ type: "success", text: "Password changed successfully" });
      setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
    } catch (err) {
      setPwMessage({ type: "error", text: err.response?.data?.error || "Failed to change password" });
    } finally {
      setPwLoading(false);
    }
  };

  if (loading) return <LoadingSpinner text="Loading profile..." />;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Profile & Security</h1>
        <p className="text-gray-500 dark:text-slate-400 mt-1">Manage your account settings</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left column — Profile card */}
        <div className="lg:col-span-1 space-y-6">
          {/* User card */}
          <div className="card p-6 text-center">
            <div className="w-16 h-16 bg-navy-100 dark:bg-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <span className="text-xl font-bold text-navy-700 dark:text-navy-300">
                {user?.first_name?.[0]}{user?.last_name?.[0]}
              </span>
            </div>
            <h2 className="text-lg font-semibold text-navy-900 dark:text-white">{user?.first_name} {user?.last_name}</h2>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-0.5">@{user?.username}</p>
            {user?.role === "admin" && (
              <span className="inline-block mt-2 text-[10px] font-semibold uppercase tracking-wider px-2.5 py-0.5 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-full border border-red-200/60 dark:border-red-800/40">Admin</span>
            )}
          </div>

          {/* Account info */}
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <CreditCard className="w-4 h-4 text-navy-700 dark:text-navy-300" />
              <h3 className="text-sm font-semibold text-navy-900 dark:text-white">Account Information</h3>
            </div>
            <div className="space-y-3">
              {[
                { label: "Email", value: profile?.email },
                { label: "Role", value: user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1) },
                { label: "Status", value: "Active", highlight: true },
                { label: "Joined", value: profile?.created_at ? new Date(profile.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "N/A" },
              ].map((item) => (
                <div key={item.label} className="flex justify-between items-center py-2 border-b border-gray-50 dark:border-slate-700/30 last:border-0">
                  <span className="text-xs text-gray-500 dark:text-slate-400">{item.label}</span>
                  {item.highlight ? (
                    <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">{item.value}</span>
                  ) : (
                    <span className="text-sm font-medium text-navy-900 dark:text-white">{item.value}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right column — Security */}
        <div className="lg:col-span-2 space-y-6">
          {/* Security Status */}
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-5">
              <Shield className="w-4 h-4 text-navy-700 dark:text-navy-300" />
              <h3 className="text-sm font-semibold text-navy-900 dark:text-white">Security Status</h3>
            </div>
            <div className="grid sm:grid-cols-3 gap-4">
              {[
                { label: "Account Protected", icon: Shield, color: "text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 dark:text-emerald-400" },
                { label: "Password Secured", icon: Lock, color: "text-accent-600 bg-accent-50 dark:bg-accent-900/20 dark:text-accent-400" },
                { label: "Activity Logged", icon: Clock, color: "text-purple-600 bg-purple-50 dark:bg-purple-900/20 dark:text-purple-400" },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-900">
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${item.color}`}>
                    <item.icon className="w-4 h-4" />
                  </div>
                  <span className="text-sm font-medium text-navy-900 dark:text-white">{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Change Password */}
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-5">
              <Key className="w-4 h-4 text-navy-700 dark:text-navy-300" />
              <h3 className="text-sm font-semibold text-navy-900 dark:text-white">Change Password</h3>
            </div>

            {pwMessage.text && (
              <Alert type={pwMessage.type} message={pwMessage.text} onClose={() => setPwMessage({ type: "", text: "" })} />
            )}

            <form onSubmit={handlePasswordChange} className="space-y-4 mt-4">
              <div>
                <label className="label">Current Password</label>
                <div className="relative">
                  <input
                    type={showCurrentPw ? "text" : "password"}
                    value={passwordForm.current_password}
                    onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                    required
                    className="input-field !pr-11"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrentPw(!showCurrentPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 transition-colors"
                  >
                    {showCurrentPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="label">New Password</label>
                <div className="relative">
                  <input
                    type={showNewPw ? "text" : "password"}
                    value={passwordForm.new_password}
                    onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                    required
                    className="input-field !pr-11"
                    placeholder="Min. 8 characters"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPw(!showNewPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300 transition-colors"
                  >
                    {showNewPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="label">Confirm New Password</label>
                <input
                  type="password"
                  value={passwordForm.confirm_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                  required
                  className="input-field"
                  autoComplete="new-password"
                />
              </div>
              <button type="submit" disabled={pwLoading} className="btn-primary">
                {pwLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Changing...
                  </>
                ) : (
                  <>
                    <Lock className="w-4 h-4" />
                    Update Password
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Login Activity */}
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-5">
              <Clock className="w-4 h-4 text-navy-700 dark:text-navy-300" />
              <h3 className="text-sm font-semibold text-navy-900 dark:text-white">Recent Login Activity</h3>
            </div>
            <div className="divide-y divide-gray-50 dark:divide-slate-700/30">
              {loginHistory.length === 0 ? (
                <div className="py-8 text-center">
                  <p className="text-sm text-gray-500 dark:text-slate-400">No login history available</p>
                </div>
              ) : (
                loginHistory.map((l) => (
                  <div key={l.id} className="py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                        l.success ? "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400" : "bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400"
                      }`}>
                        {l.success ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-navy-900 dark:text-white">
                          {l.success ? "Successful login" : "Failed login attempt"}
                        </p>
                        <p className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">
                          IP: {l.source_ip}
                          {l.failure_reason && ` • ${l.failure_reason}`}
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-gray-400 dark:text-slate-500 whitespace-nowrap ml-4">
                      {new Date(l.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                      <span className="ml-1">{new Date(l.created_at).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}</span>
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
