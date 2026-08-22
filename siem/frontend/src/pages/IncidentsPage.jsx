import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { socket } from '../services/socket';
import SeverityBadge from '../components/SeverityBadge';
import { GitPullRequest, ArrowRight, RefreshCw } from 'lucide-react';

const IncidentsPage = () => {
  const [incidents, setIncidents] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      const res = await api.get('/incidents', {
        params: { status: statusFilter || undefined }
      });
      setIncidents(res.data.incidents);
    } catch (err) {
      console.error('Failed to fetch incidents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();

    const handleIncidentUpdated = (updatedInc) => {
      setIncidents((prev) => {
        const idx = prev.findIndex((i) => i.id === updatedInc.id);
        if (idx >= 0) {
          const next = [...prev];
          next[idx] = updatedInc;
          return next;
        }
        return [updatedInc, ...prev];
      });
    };

    socket.on('incident_updated', handleIncidentUpdated);
    return () => socket.off('incident_updated', handleIncidentUpdated);
  }, [statusFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Incidents Center</h1>
          <p className="text-xs text-slate-400">Correlated security threat clusters and multi-stage campaign tracking</p>
        </div>
        <button
          onClick={fetchIncidents}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Incidents</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-panel rounded-xl p-4 flex items-center gap-2">
        {['', 'OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED'].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
              statusFilter === st
                ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                : 'bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            {st === '' ? 'All Statuses' : st}
          </button>
        ))}
      </div>

      {/* Incidents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {incidents.map((inc) => (
          <div key={inc.id} className="glass-panel rounded-xl p-5 hover:border-slate-700 transition-all flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <GitPullRequest className="w-4 h-4 text-cyan-400" />
                  <span className="font-mono text-xs font-bold text-slate-400">INC-{inc.id}</span>
                  <SeverityBadge severity={inc.severity} />
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-slate-800 border border-slate-700 text-slate-300">
                  {inc.status}
                </span>
              </div>

              <h3 className="font-bold text-slate-100 text-base mb-1">{inc.title}</h3>
              <p className="text-xs text-slate-400 line-clamp-2 mb-4">{inc.description}</p>
            </div>

            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <div className="flex gap-4 font-mono text-[11px] text-slate-300">
                <span>IP: {inc.source_ip || 'N/A'}</span>
                <span>User: {inc.affected_user || 'N/A'}</span>
                <span className="text-amber-400 font-bold">Alerts: {inc.alert_count}</span>
              </div>

              <Link
                to={`/incidents/${inc.id}`}
                className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 font-semibold"
              >
                View Campaign <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default IncidentsPage;
