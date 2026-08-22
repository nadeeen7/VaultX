import { useState, useEffect } from "react";
import { getTransactions } from "../services/api.js";
import LoadingSpinner from "../components/LoadingSpinner.jsx";
import { ArrowUpRight, ArrowDownLeft, History, ChevronLeft, ChevronRight } from "lucide-react";

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await getTransactions({ page, per_page: 15 });
        setTransactions(res.data.transactions);
        setTotalPages(res.data.pages);
      } catch (err) {
        console.error("Failed to load transactions", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [page]);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Transaction History</h1>
        <p className="text-gray-500 dark:text-slate-400 mt-1">View all your account transactions</p>
      </div>

      {loading ? (
        <LoadingSpinner text="Loading transactions..." />
      ) : (
        <div className="card overflow-hidden">
          {/* Desktop table */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100 dark:border-slate-700/50">
                  <th className="text-left px-6 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Reference</th>
                  <th className="text-left px-6 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Date</th>
                  <th className="text-left px-6 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Type</th>
                  <th className="text-left px-6 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Description</th>
                  <th className="text-right px-6 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Amount</th>
                  <th className="text-center px-6 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 dark:divide-slate-700/30">
                {transactions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-16 text-center">
                      <div className="w-12 h-12 bg-gray-100 dark:bg-slate-700 rounded-xl flex items-center justify-center mx-auto mb-3">
                        <History className="w-6 h-6 text-gray-300 dark:text-slate-500" />
                      </div>
                      <p className="text-sm font-medium text-gray-500 dark:text-slate-400">No transactions found</p>
                      <p className="text-xs text-gray-400 dark:text-slate-500 mt-1">Your transaction history will appear here</p>
                    </td>
                  </tr>
                ) : (
                  transactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-gray-50/50 dark:hover:bg-slate-700/20 transition-colors">
                      <td className="px-6 py-4 font-mono text-xs text-gray-500 dark:text-slate-400">{tx.reference || tx.id.slice(0, 8)}</td>
                      <td className="px-6 py-4 text-sm text-gray-600 dark:text-slate-300">
                        {new Date(tx.created_at).toLocaleDateString("en-US", {
                          month: "short", day: "numeric", year: "numeric",
                        })}
                        <span className="text-gray-400 dark:text-slate-500 ml-1">
                          {new Date(tx.created_at).toLocaleTimeString("en-US", {
                            hour: "2-digit", minute: "2-digit",
                          })}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${
                          tx.transaction_type === "transfer_out"
                            ? "text-red-600 dark:text-red-400"
                            : "text-emerald-600 dark:text-emerald-400"
                        }`}>
                          {tx.transaction_type === "transfer_out"
                            ? <ArrowUpRight className="w-3.5 h-3.5" />
                            : <ArrowDownLeft className="w-3.5 h-3.5" />
                          }
                          {tx.transaction_type === "transfer_out" ? "Outgoing" : "Incoming"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 dark:text-slate-300">
                        {tx.description}
                        {tx.recipient_name && (
                          <span className="text-gray-400 dark:text-slate-500 ml-1">→ {tx.recipient_name}</span>
                        )}
                      </td>
                      <td className={`px-6 py-4 text-right font-semibold text-sm ${
                        tx.transaction_type === "transfer_out" ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"
                      }`}>
                        {tx.transaction_type === "transfer_out" ? "−" : "+"}${tx.amount.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          tx.status === "completed" ? "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400" :
                          tx.status === "pending" ? "bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400" :
                          "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400"
                        }`}>
                          {tx.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden divide-y divide-gray-50 dark:divide-slate-700/30">
            {transactions.length === 0 ? (
              <div className="px-6 py-16 text-center">
                <div className="w-12 h-12 bg-gray-100 dark:bg-slate-700 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <History className="w-6 h-6 text-gray-300 dark:text-slate-500" />
                </div>
                <p className="text-sm font-medium text-gray-500 dark:text-slate-400">No transactions found</p>
              </div>
            ) : (
              transactions.map((tx) => (
                <div key={tx.id} className="px-4 py-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2.5">
                      <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                        tx.transaction_type === "transfer_out" ? "bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400" : "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400"
                      }`}>
                        {tx.transaction_type === "transfer_out"
                          ? <ArrowUpRight className="w-4 h-4" />
                          : <ArrowDownLeft className="w-4 h-4" />
                        }
                      </div>
                      <div>
                        <p className="text-sm font-medium text-navy-900 dark:text-white">{tx.recipient_name || tx.description}</p>
                        <p className="text-xs text-gray-400 dark:text-slate-500">{tx.reference}</p>
                      </div>
                    </div>
                    <p className={`font-semibold text-sm ${
                      tx.transaction_type === "transfer_out" ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"
                    }`}>
                      {tx.transaction_type === "transfer_out" ? "−" : "+"}${tx.amount.toFixed(2)}
                    </p>
                  </div>
                  <div className="flex items-center justify-between pl-[46px]">
                    <span className="text-xs text-gray-400 dark:text-slate-500">
                      {new Date(tx.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    </span>
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

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100 dark:border-slate-700/50">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary !px-3 !py-1.5 text-xs"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                Previous
              </button>
              <span className="text-sm text-gray-500 dark:text-slate-400">
                Page <span className="font-medium text-navy-900 dark:text-white">{page}</span> of <span className="font-medium text-navy-900 dark:text-white">{totalPages}</span>
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn-secondary !px-3 !py-1.5 text-xs"
              >
                Next
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
