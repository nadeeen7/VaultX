import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getAdminStats, getAdminUsers, getAdminTransactions, getAdminSecurityEvents } from "../services/api.js";
import LoadingSpinner from "../components/LoadingSpinner.jsx";
import {
  Users,
  UserCheck,
  AlertTriangle,
  ArrowLeftRight,
  ArrowUpRight,
  ArrowDownLeft,
  ChevronRight,
  Shield,
  Activity,
} from "lucide-react";

export default function AdminDashboardPage() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [statsRes, usersRes, txRes, evRes] = await Promise.all([
          getAdminStats(),
          getAdminUsers({ per_page: 5 }),
          getAdminTransactions({ per_page: 5 }),
          getAdminSecurityEvents({ per_page: 10 }),
        ]);
        setStats(statsRes.data);
        setUsers(usersRes.data.users);
        setTransactions(txRes.data.transactions);
        setEvents(evRes.data.events);
      } catch (err) {
        console.error("Failed to load admin dashboard", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <LoadingSpinner text="Loading admin dashboard..." />;

  const statCards = stats ? [
    { label: "Total Users", value: stats.total_users, icon: Users, color: "text-accent-600 bg-accent-50 dark:bg-accent-900/20 dark:text-accent-400" },
    { label: "Active Users", value: stats.active_users, icon: UserCheck, color: "text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 dark:text-emerald-400" },
    { label: "Locked Accounts", value: stats.locked_users, icon: AlertTriangle, color: "text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400" },
    { label: "Transactions", value: stats.total_transactions, icon: ArrowLeftRight, color: "text-purple-600 bg-purple-50 dark:bg-purple-900/20 dark:text-purple-400" },
  ] : [];

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Admin Dashboard</h1>
        <p className="text-gray-500 dark:text-slate-400 mt-1">System overview and security monitoring</p>
      </div>

      {/* Stats Grid */}
      {stats && (
        <>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {statCards.map((s) => (
              <div key={s.label} className="card p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500 dark:text-slate-400 font-medium">{s.label}</p>
                    <p className="text-2xl font-bold text-navy-900 dark:text-white mt-1">{s.value}</p>
                  </div>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${s.color}`}>
                    <s.icon className="w-5 h-5" />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Alert stats */}
          <div className="grid sm:grid-cols-2 gap-4 mb-8">
            <div className="card p-5 border-l-4 border-l-red-500">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-red-50 dark:bg-red-900/20 rounded-xl flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-slate-400 font-medium">Failed Logins (24h)</p>
                  <p className="text-xl font-bold text-red-600 dark:text-red-400">{stats.failed_logins_24h}</p>
                </div>
              </div>
            </div>
            <div className="card p-5 border-l-4 border-l-amber-500">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-amber-50 dark:bg-amber-900/20 rounded-xl flex items-center justify-center">
                  <Activity className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-slate-400 font-medium">Security Events (24h)</p>
                  <p className="text-xl font-bold text-amber-600 dark:text-amber-400">{stats.security_events_24h}</p>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent Users */}
        <div className="card">
          <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-700/50 flex items-center justify-between">
            <h3 className="font-semibold text-navy-900 dark:text-white">Recent Users</h3>
            <Link to="/admin/users" className="text-sm font-medium text-accent-600 hover:text-accent-700 dark:text-accent-400 dark:hover:text-accent-300 flex items-center gap-1">
              View All <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-gray-50 dark:divide-slate-700/30">
            {users.map((u) => (
              <div key={u.id} className="px-6 py-3.5 flex items-center justify-between hover:bg-gray-50/50 dark:hover:bg-slate-700/20 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-navy-100 dark:bg-slate-700 rounded-xl flex items-center justify-center">
                    <span className="text-xs font-semibold text-navy-700 dark:text-navy-300">{u.first_name?.[0]}{u.last_name?.[0]}</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-navy-900 dark:text-white">{u.first_name} {u.last_name}</p>
                    <p className="text-xs text-gray-400 dark:text-slate-500">@{u.username}</p>
                  </div>
                </div>
                <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${
                  u.is_active ? "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400" : "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400"
                }`}>
                  {u.is_active ? "Active" : "Disabled"}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Security Events */}
        <div className="card">
          <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-700/50 flex items-center justify-between">
            <h3 className="font-semibold text-navy-900 dark:text-white">Security Events</h3>
            <Link to="/admin/security" className="text-sm font-medium text-accent-600 hover:text-accent-700 dark:text-accent-400 dark:hover:text-accent-300 flex items-center gap-1">
              View All <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-gray-50 dark:divide-slate-700/30">
            {events.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <div className="w-10 h-10 bg-gray-100 dark:bg-slate-700 rounded-xl flex items-center justify-center mx-auto mb-2">
                  <Shield className="w-5 h-5 text-gray-300 dark:text-slate-500" />
                </div>
                <p className="text-sm text-gray-500 dark:text-slate-400">No security events</p>
              </div>
            ) : (
              events.map((ev) => (
                <div key={ev.event_id} className="px-6 py-3.5 hover:bg-gray-50/50 dark:hover:bg-slate-700/20 transition-colors">
                  <div className="flex items-center justify-between">
                    <span className={`text-xs font-mono font-medium px-2 py-0.5 rounded ${
                      ev.status === "SUCCESS" ? "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400" :
                      ev.status === "FAILED" ? "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400" :
                      ev.status === "BLOCKED" ? "bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400" :
                      "bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300"
                    }`}>
                      {ev.event_type}
                    </span>
                    <span className="text-xs text-gray-400 dark:text-slate-500">
                      {new Date(ev.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-slate-400 mt-1.5">
                    {ev.username || "system"} • {ev.source_ip}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="card lg:col-span-2">
          <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-700/50">
            <h3 className="font-semibold text-navy-900 dark:text-white">Recent Transactions</h3>
          </div>
          <div className="divide-y divide-gray-50 dark:divide-slate-700/30">
            {transactions.map((tx) => (
              <div key={tx.id} className="px-6 py-3.5 flex items-center justify-between hover:bg-gray-50/50 dark:hover:bg-slate-700/20 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                    tx.transaction_type === "transfer_out" ? "bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400" : "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400"
                  }`}>
                    {tx.transaction_type === "transfer_out"
                      ? <ArrowUpRight className="w-4 h-4" />
                      : <ArrowDownLeft className="w-4 h-4" />
                    }
                  </div>
                  <div>
                    <p className="text-sm font-medium text-navy-900 dark:text-white">{tx.description || tx.transaction_type}</p>
                    <p className="text-xs text-gray-400 dark:text-slate-500">{tx.reference} • {new Date(tx.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}</p>
                  </div>
                </div>
                <span className={`font-semibold text-sm ${
                  tx.transaction_type === "transfer_out" ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"
                }`}>
                  {tx.transaction_type === "transfer_out" ? "−" : "+"}${tx.amount.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
