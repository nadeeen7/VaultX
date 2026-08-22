import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Cpu, RefreshCw, AlertTriangle, ShieldCheck } from 'lucide-react';
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  Cell
} from 'recharts';

const AnalyticsPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMLAnalytics = async () => {
    setLoading(true);
    try {
      const res = await api.get('/analytics/ml');
      setData(res.data);
    } catch (err) {
      console.error('Failed to fetch ML analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMLAnalytics();
  }, []);

  const anomalies = data?.recent_anomalies || [];
  const summary = data?.summary || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Behavioral Analytics & Machine Learning</h1>
          <p className="text-xs text-slate-400">scikit-learn Isolation Forest anomaly scoring and feature vector telemetry</p>
        </div>
        <button
          onClick={fetchMLAnalytics}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retrain / Refresh</span>
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel rounded-xl p-5">
          <span className="text-xs text-slate-400 font-semibold uppercase">Total Events Analyzed</span>
          <h3 className="text-2xl font-extrabold font-mono text-slate-100 mt-1">{summary.total_scanned || 0}</h3>
        </div>
        <div className="glass-panel rounded-xl p-5">
          <span className="text-xs text-slate-400 font-semibold uppercase">Isolation Forest Flagged Anomalies</span>
          <h3 className="text-2xl font-extrabold font-mono text-rose-400 mt-1">{summary.flagged_anomalies || 0}</h3>
        </div>
        <div className="glass-panel rounded-xl p-5">
          <span className="text-xs text-slate-400 font-semibold uppercase">Anomaly Detection Ratio</span>
          <h3 className="text-2xl font-extrabold font-mono text-cyan-400 mt-1">{((summary.anomaly_ratio || 0) * 100).toFixed(1)}%</h3>
        </div>
      </div>

      {/* Feature List & Predictions */}
      <div className="glass-panel rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <Cpu className="w-4 h-4 text-emerald-400" />
          Isolation Forest Anomaly Telemetry Log
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-3">Time</th>
                <th className="p-3">Source IP</th>
                <th className="p-3">User</th>
                <th className="p-3">Anomaly Score</th>
                <th className="p-3">Model Decision</th>
                <th className="p-3">Extracted Feature Reasoning</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {anomalies.map((anom) => (
                <tr key={anom.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-3 font-mono text-slate-400">
                    {anom.timestamp ? new Date(anom.timestamp).toLocaleTimeString() : 'N/A'}
                  </td>
                  <td className="p-3 font-mono text-slate-200">{anom.source_ip}</td>
                  <td className="p-3 text-slate-300">{anom.username || 'N/A'}</td>
                  <td className="p-3 font-mono font-bold text-amber-400">
                    {(anom.anomaly_score * 100).toFixed(0)}%
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-semibold ${
                      anom.is_anomaly ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    }`}>
                      {anom.is_anomaly ? 'ANOMALOUS' : 'NORMAL'}
                    </span>
                  </td>
                  <td className="p-3 text-slate-300 max-w-md">{anom.reasoning}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
