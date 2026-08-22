import { useState, useEffect } from "react";
import { getAdminSecurityEvents } from "../services/api.js";
import LoadingSpinner from "../components/LoadingSpinner.jsx";
import { Shield, Filter, ChevronLeft, ChevronRight } from "lucide-react";

const EVENT_TYPES = [
  "LOGIN_SUCCESS", "LOGIN_FAILED", "LOGOUT", "ACCOUNT_LOCKED",
  "TRANSFER_CREATED", "TRANSFER_FAILED", "PASSWORD_CHANGE",
  "UNAUTHORIZED_ACCESS", "SUSPICIOUS_REQUEST", "ADMIN_LOGIN",
  "ADMIN_LOGIN_FAILED", "ACCOUNT_CREATED", "PASSWORD_CHANGE_FAILED",
];

export default function AdminSecurityPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({ event_type: "", status: "", username: "" });

  const loadEvents = async () => {
    setLoading(true);
    try {
      const params = { page, per_page: 20 };
      if (filters.event_type) params.event_type = filters.event_type;
      if (filters.status) params.status = filters.status;
      if (filters.username) params.username = filters.username;

      const res = await getAdminSecurityEvents(params);
      setEvents(res.data.events);
      setTotalPages(res.data.pages);
    } catch (err) {
      console.error("Failed to load security events", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadEvents(); }, [page, filters]);

  const statusColor = (status) => {
    switch (status) {
      case "SUCCESS": return "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400";
      case "FAILED": return "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400";
      case "BLOCKED": return "bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400";
      default: return "bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300";
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Security Events</h1>
        <p className="text-gray-500 dark:text-slate-400 mt-1">Monitor security events across the system</p>
      </div>

      {/* Filters */}
      <div className="card p-4 mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-gray-400 dark:text-slate-500" />
          <span className="text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Filters</span>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="flex-1 min-w-[180px]">
            <label className="text-[11px] text-gray-500 dark:text-slate-400 font-medium mb-1 block">Event Type</label>
            <select
              value={filters.event_type}
              onChange={(e) => { setFilters({ ...filters, event_type: e.target.value }); setPage(1); }}
              className="w-full px-3 py-2 border border-gray-200 dark:border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-500 outline-none bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100"
            >
              <option value="">All Events</option>
              {EVENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="min-w-[140px]">
            <label className="text-[11px] text-gray-500 dark:text-slate-400 font-medium mb-1 block">Status</label>
            <select
              value={filters.status}
              onChange={(e) => { setFilters({ ...filters, status: e.target.value }); setPage(1); }}
              className="w-full px-3 py-2 border border-gray-200 dark:border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-500 outline-none bg-white dark:bg-slate-800 text-gray-900 dark:text-gray-100"
            >
              <option value="">All Statuses</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="FAILED">FAILED</option>
              <option value="BLOCKED">BLOCKED</option>
            </select>
          </div>
          <div className="flex-1 min-w-[160px]">
            <label className="text-[11px] text-gray-500 dark:text-slate-400 font-medium mb-1 block">Username</label>
            <input
              type="text"
              value={filters.username}
              onChange={(e) => { setFilters({ ...filters, username: e.target.value }); setPage(1); }}
              placeholder="Filter by username"
              className="input-field"
            />
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner text="Loading events..." />
      ) : (
        <div className="card overflow-hidden">
          {/* Desktop table */}
          <div className="hidden lg:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100 dark:border-slate-700/50">
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Event</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Timestamp</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">User</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">IP Address</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Endpoint</th>
                  <th className="text-center px-5 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Status</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 dark:divide-slate-700/30">
                {events.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-16 text-center">
                      <div className="w-12 h-12 bg-gray-100 dark:bg-slate-700 rounded-xl flex items-center justify-center mx-auto mb-3">
                        <Shield className="w-6 h-6 text-gray-300 dark:text-slate-500" />
                      </div>
                      <p className="text-sm font-medium text-gray-500 dark:text-slate-400">No events found</p>
                    </td>
                  </tr>
                ) : (
                  events.map((ev) => (
                    <tr key={ev.event_id} className="hover:bg-gray-50/50 dark:hover:bg-slate-700/20 transition-colors">
                      <td className="px-5 py-3.5">
                        <span className="font-mono text-xs font-medium text-navy-700 dark:text-navy-300 bg-navy-50 dark:bg-navy-900/30 px-2 py-0.5 rounded">
                          {ev.event_type}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-xs text-gray-600 dark:text-slate-300">
                        {new Date(ev.timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                        <span className="text-gray-400 dark:text-slate-500 ml-1">
                          {new Date(ev.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-sm text-gray-600 dark:text-slate-300">{ev.username || "—"}</td>
                      <td className="px-5 py-3.5 text-xs font-mono text-gray-500 dark:text-slate-400">{ev.source_ip}</td>
                      <td className="px-5 py-3.5 text-xs text-gray-500 dark:text-slate-400">
                        <span className="text-gray-400 dark:text-slate-500">{ev.http_method}</span> {ev.endpoint}
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${statusColor(ev.status)}`}>
                          {ev.status}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-xs text-gray-400 dark:text-slate-500 max-w-[200px] truncate">
                        {ev.metadata && Object.keys(ev.metadata).length > 0
                          ? JSON.stringify(ev.metadata)
                          : "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="lg:hidden divide-y divide-gray-50 dark:divide-slate-700/30">
            {events.length === 0 ? (
              <div className="px-6 py-16 text-center">
                <div className="w-12 h-12 bg-gray-100 dark:bg-slate-700 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <Shield className="w-6 h-6 text-gray-300 dark:text-slate-500" />
                </div>
                <p className="text-sm font-medium text-gray-500 dark:text-slate-400">No events found</p>
              </div>
            ) : (
              events.map((ev) => (
                <div key={ev.event_id} className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-medium text-navy-700 dark:text-navy-300 bg-navy-50 dark:bg-navy-900/30 px-2 py-0.5 rounded">
                      {ev.event_type}
                    </span>
                    <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${statusColor(ev.status)}`}>
                      {ev.status}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500 dark:text-slate-400 mb-1">
                    <span>{ev.username || "—"}</span>
                    <span className="font-mono">{ev.source_ip}</span>
                  </div>
                  <div className="text-[11px] text-gray-400 dark:text-slate-500">
                    {new Date(ev.timestamp).toLocaleString()}
                    <span className="ml-2">{ev.http_method} {ev.endpoint}</span>
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
