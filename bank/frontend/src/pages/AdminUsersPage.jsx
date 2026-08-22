import { useState, useEffect } from "react";
import { getAdminUsers, toggleUserStatus } from "../services/api.js";
import LoadingSpinner from "../components/LoadingSpinner.jsx";
import Alert from "../components/Alert.jsx";
import { Users, UserX, UserCheck } from "lucide-react";

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ type: "", text: "" });

  const loadUsers = async () => {
    try {
      const res = await getAdminUsers({ per_page: 50 });
      setUsers(res.data.users);
    } catch (err) {
      console.error("Failed to load users", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadUsers(); }, []);

  const handleToggle = async (userId) => {
    try {
      const res = await toggleUserStatus(userId);
      setMessage({ type: "success", text: res.data.message });
      loadUsers();
    } catch (err) {
      setMessage({ type: "error", text: err.response?.data?.error || "Failed to toggle status" });
    }
  };

  if (loading) return <LoadingSpinner text="Loading users..." />;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-navy-900 dark:text-white">User Management</h1>
        <p className="text-gray-500 dark:text-slate-400 mt-1">Manage and monitor user accounts</p>
      </div>

      {message.text && (
        <div className="mb-6">
          <Alert type={message.type} message={message.text} onClose={() => setMessage({ type: "", text: "" })} />
        </div>
      )}

      {/* Desktop table */}
      <div className="card overflow-hidden">
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 dark:border-slate-700/50">
                <th className="text-left px-6 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">User</th>
                <th className="text-left px-6 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Email</th>
                <th className="text-left px-6 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Role</th>
                <th className="text-left px-6 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Balance</th>
                <th className="text-center px-6 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Status</th>
                <th className="text-center px-6 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-slate-700/30">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50/50 dark:hover:bg-slate-700/20 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 bg-navy-100 dark:bg-slate-700 rounded-xl flex items-center justify-center">
                        <span className="text-xs font-semibold text-navy-700 dark:text-navy-300">{u.first_name?.[0]}{u.last_name?.[0]}</span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-navy-900 dark:text-white">{u.first_name} {u.last_name}</p>
                        <p className="text-xs text-gray-400 dark:text-slate-500">@{u.username}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 dark:text-slate-300">{u.email}</td>
                  <td className="px-6 py-4">
                    <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${
                      u.role === "admin" ? "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400" : "bg-accent-50 dark:bg-accent-900/20 text-accent-700 dark:text-accent-400"
                    }`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm font-medium text-navy-900 dark:text-white">
                    {u.account ? `$${u.account.balance.toFixed(2)}` : "N/A"}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex items-center justify-center gap-1.5">
                      <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${
                        u.is_active ? "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400" : "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400"
                      }`}>
                        {u.is_active ? "Active" : "Disabled"}
                      </span>
                      {u.is_locked && (
                        <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400">
                          Locked
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    {u.role !== "admin" && (
                      <button
                        onClick={() => handleToggle(u.id)}
                        className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
                          u.is_active
                            ? "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30"
                            : "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/30"
                        }`}
                      >
                        {u.is_active ? <UserX className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                        {u.is_active ? "Disable" : "Enable"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Mobile cards */}
        <div className="md:hidden divide-y divide-gray-50 dark:divide-slate-700/30">
          {users.map((u) => (
            <div key={u.id} className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-navy-100 dark:bg-slate-700 rounded-xl flex items-center justify-center">
                    <span className="text-sm font-semibold text-navy-700 dark:text-navy-300">{u.first_name?.[0]}{u.last_name?.[0]}</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-navy-900 dark:text-white">{u.first_name} {u.last_name}</p>
                    <p className="text-xs text-gray-400 dark:text-slate-500">@{u.username}</p>
                  </div>
                </div>
                <div className="flex gap-1.5">
                  <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                    u.role === "admin" ? "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400" : "bg-accent-50 dark:bg-accent-900/20 text-accent-700 dark:text-accent-400"
                  }`}>
                    {u.role}
                  </span>
                  <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                    u.is_active ? "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400" : "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400"
                  }`}>
                    {u.is_active ? "Active" : "Disabled"}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500 dark:text-slate-400">{u.email}</span>
                <span className="text-sm font-semibold text-navy-900 dark:text-white">
                  {u.account ? `$${u.account.balance.toFixed(2)}` : "N/A"}
                </span>
              </div>
              {u.role !== "admin" && (
                <div className="mt-3">
                  <button
                    onClick={() => handleToggle(u.id)}
                    className={`w-full text-xs font-medium px-3 py-2 rounded-lg transition-colors ${
                      u.is_active
                        ? "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30"
                        : "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/30"
                    }`}
                  >
                    {u.is_active ? "Disable Account" : "Enable Account"}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
