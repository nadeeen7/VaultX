import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { getProfile, getTransactions } from "../services/api.js";
import LoadingSpinner, { SkeletonLines } from "../components/LoadingSpinner.jsx";
import {
  ArrowUpRight,
  ArrowDownLeft,
  ArrowLeftRight,
  History,
  Shield,
  CreditCard,
  ChevronRight,
  TrendingUp,
} from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [profileRes, txRes] = await Promise.all([
          getProfile(),
          getTransactions({ per_page: 5 }),
        ]);
        setProfile(profileRes.data);
        setTransactions(txRes.data.transactions);
      } catch (err) {
        console.error("Failed to load dashboard", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <LoadingSpinner text="Loading your dashboard..." />;

  const account = profile?.account;
  const greeting = (() => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  })();

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-navy-900 dark:text-white">
          {greeting}, {user?.first_name}
        </h1>
        <p className="text-gray-500 dark:text-slate-400 mt-1">Here&apos;s your financial overview</p>
      </div>

      {/* Balance Card + Quick Actions */}
      <div className="grid lg:grid-cols-3 gap-6 mb-8">
        {/* Premium Balance Card */}
        <div className="lg:col-span-2 bg-navy-900 rounded-2xl p-6 sm:p-8 text-white relative overflow-hidden">
          {/* Decorative gradient */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-accent-600/10 rounded-full -translate-y-32 translate-x-32" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-accent-500/5 rounded-full translate-y-24 -translate-x-24" />

          <div className="relative">
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-gray-400 text-sm font-medium">Total Balance</p>
                <p className="text-3xl sm:text-4xl font-bold mt-1 tracking-tight">
                  ${account?.balance?.toLocaleString("en-US", { minimumFractionDigits: 2 }) || "0.00"}
                </p>
              </div>
              <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center backdrop-blur-sm">
                <CreditCard className="w-6 h-6 text-white/80" />
              </div>
            </div>

            <div className="flex items-end justify-between">
              <div>
                <p className="text-gray-400 text-xs">Available Balance</p>
                <p className="text-lg font-semibold mt-0.5">
                  ${account?.balance?.toLocaleString("en-US", { minimumFractionDigits: 2 }) || "0.00"}
                </p>
              </div>
              <div className="text-right">
                <p className="text-gray-400 text-xs">Account</p>
                <p className="font-mono text-sm font-medium mt-0.5">
                  •••• {account?.account_number?.slice(-4) || "0000"}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-navy-900 dark:text-white mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            <Link
              to="/transfer"
              className="flex flex-col items-center gap-2 p-4 rounded-xl bg-navy-50 dark:bg-navy-900/30 hover:bg-navy-100 dark:hover:bg-navy-900/50 transition-colors group"
            >
              <div className="w-10 h-10 bg-navy-800 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform">
                <ArrowUpRight className="w-5 h-5 text-white" />
              </div>
              <span className="text-xs font-medium text-navy-800 dark:text-navy-300">Send Money</span>
            </Link>
            <Link
              to="/transactions"
              className="flex flex-col items-center gap-2 p-4 rounded-xl bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors group"
            >
              <div className="w-10 h-10 bg-gray-700 dark:bg-slate-600 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform">
                <History className="w-5 h-5 text-white" />
              </div>
              <span className="text-xs font-medium text-gray-700 dark:text-slate-300">History</span>
            </Link>
            <Link
              to="/profile"
              className="flex flex-col items-center gap-2 p-4 rounded-xl bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors group"
            >
              <div className="w-10 h-10 bg-gray-700 dark:bg-slate-600 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="text-xs font-medium text-gray-700 dark:text-slate-300">Security</span>
            </Link>
            <Link
              to="/profile"
              className="flex flex-col items-center gap-2 p-4 rounded-xl bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors group"
            >
              <div className="w-10 h-10 bg-gray-700 dark:bg-slate-600 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <span className="text-xs font-medium text-gray-700 dark:text-slate-300">Account</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Account Details + Recent Transactions */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Recent Transactions */}
        <div className="lg:col-span-2 card">
          <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-700/50 flex items-center justify-between">
            <h3 className="font-semibold text-navy-900 dark:text-white">Recent Transactions</h3>
            <Link
              to="/transactions"
              className="text-sm font-medium text-accent-600 hover:text-accent-700 dark:text-accent-400 dark:hover:text-accent-300 flex items-center gap-1"
            >
              View All
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-gray-50 dark:divide-slate-700/30">
            {transactions.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <div className="w-12 h-12 bg-gray-100 dark:bg-slate-700 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <History className="w-6 h-6 text-gray-300 dark:text-slate-500" />
                </div>
                <p className="text-sm font-medium text-gray-500 dark:text-slate-400">No transactions yet</p>
                <p className="text-xs text-gray-400 dark:text-slate-500 mt-1">Your transactions will appear here</p>
              </div>
            ) : (
              transactions.map((tx) => (
                <div key={tx.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50/50 dark:hover:bg-slate-700/20 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      tx.transaction_type === "transfer_out"
                        ? "bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400"
                        : "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400"
                    }`}>
                      {tx.transaction_type === "transfer_out"
                        ? <ArrowUpRight className="w-5 h-5" />
                        : <ArrowDownLeft className="w-5 h-5" />
                      }
                    </div>
                    <div>
                      <p className="text-sm font-medium text-navy-900 dark:text-white">
                        {tx.recipient_name || tx.description}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">
                        {tx.reference} • {new Date(tx.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-semibold ${
                      tx.transaction_type === "transfer_out" ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"
                    }`}>
                      {tx.transaction_type === "transfer_out" ? "−" : "+"}${tx.amount.toFixed(2)}
                    </p>
                    <span className={`text-[11px] font-medium ${
                      tx.status === "completed" ? "text-emerald-600 dark:text-emerald-400" :
                      tx.status === "pending" ? "text-amber-600 dark:text-amber-400" : "text-red-600 dark:text-red-400"
                    }`}>
                      {tx.status.charAt(0).toUpperCase() + tx.status.slice(1)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Account Details */}
        <div className="card p-6 h-fit">
          <h3 className="text-sm font-semibold text-navy-900 dark:text-white mb-4">Account Details</h3>
          <div className="space-y-3.5">
            {[
              { label: "Account Number", value: account?.account_number || "N/A", mono: true },
              { label: "Account Type", value: account?.account_type ? account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1) : "Checking" },
              { label: "Status", value: account?.status || "Active", status: true },
              { label: "Currency", value: account?.currency || "USD" },
              { label: "Member Since", value: profile?.created_at ? new Date(profile.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "N/A" },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between py-2 border-b border-gray-50 dark:border-slate-700/30 last:border-0">
                <span className="text-xs text-gray-500 dark:text-slate-400">{item.label}</span>
                {item.status ? (
                  <span className={`text-xs font-medium ${
                    account?.status === "active" ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"
                  }`}>
                    {item.value}
                  </span>
                ) : (
                  <span className={`text-sm font-medium text-navy-900 dark:text-white ${item.mono ? "font-mono text-xs" : ""}`}>
                    {item.value}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
