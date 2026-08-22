import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import SeverityBadge from '../components/SeverityBadge';
import {
  GitPullRequest,
  Clock,
  ShieldAlert,
  ArrowLeft,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

const IncidentDetailPage = () => {
  const { id } = useParams();
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchIncidentDetail = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/incidents/${id}`);
      setIncident(res.data.incident);
    } catch (err) {
      console.error('Failed to fetch incident detail:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidentDetail();
  }, [id]);

  const updateStatus = async (status) => {
    try {
      await api.patch(`/incidents/${id}/status`, { status });
      fetchIncidentDetail();
    } catch (err) {
      console.error('Failed to update incident status:', err);
    }
  };

  if (loading || !incident) {
    return <div className="p-8 text-center text-slate-400">Loading Incident INC-{id}...</div>;
  }

  const timeline = incident.timeline || [];
  const events = incident.events || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/incidents" className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-slate-400">INC-{incident.id}</span>
              <SeverityBadge severity={incident.severity} />
              <span className="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-slate-800 border border-slate-700 text-slate-300">
                {incident.status}
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-100 mt-0.5">{incident.title}</h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {['OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED'].map((st) => (
            <button
              key={st}
              onClick={() => updateStatus(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase ${
                incident.status === st
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Main Campaign Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Visual Attack Timeline */}
          <div className="glass-panel rounded-xl p-5">
            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-slate-800">
              <Clock className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Attack Kill Chain Timeline</h3>
            </div>

            <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
              {timeline.map((item, idx) => (
                <div key={idx} className="relative flex items-start gap-4">
                  <div className={`absolute -left-6 top-1.5 w-3 h-3 rounded-full border-2 bg-slate-900 ${
                    item.type === 'ALERT' ? 'border-rose-500' : 'border-blue-400'
                  }`} />
                  
                  <div className="glass-panel rounded-lg p-3 w-full border border-slate-800 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-slate-200">{item.event_title}</span>
                      <span className="font-mono text-[10px] text-slate-400">
                        {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : ''}
                      </span>
                    </div>
                    <p className="text-slate-400 text-[11px] mb-2">{item.details}</p>
                    <div className="flex items-center gap-3 font-mono text-[10px] text-slate-500">
                      <span>IP: {item.source_ip}</span>
                      <span>User: {item.user}</span>
                      <span className="text-cyan-400">{item.detection}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Attached Alerts Matrix */}
          <div className="glass-panel rounded-xl p-5">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-3">Correlated Alerts Matrix</h3>
            <div className="space-y-2">
              {events.map((e) => {
                const a = e.alert;
                if (!a) return null;
                return (
                  <div key={e.id} className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-3">
                      <SeverityBadge severity={a.severity} />
                      <div>
                        <span className="font-semibold text-slate-200 block">{a.title}</span>
                        <span className="text-[11px] text-slate-400">IP: {a.source_ip} • User: {a.username || 'N/A'}</span>
                      </div>
                    </div>
                    <Link to={`/alerts/${a.id}`} className="text-blue-400 hover:underline font-semibold">
                      View Alert
                    </Link>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <div className="glass-panel rounded-xl p-5 space-y-3 text-xs">
            <h3 className="font-bold text-slate-200 uppercase tracking-wider">Incident Metadata</h3>
            <div className="space-y-2 pt-2">
              <div className="flex justify-between border-b border-slate-800/80 pb-2">
                <span className="text-slate-400">Source Attacker IP:</span>
                <span className="font-mono text-slate-200 font-semibold">{incident.source_ip || 'N/A'}</span>
              </div>
              <div className="flex justify-between border-b border-slate-800/80 pb-2">
                <span className="text-slate-400">Target User Account:</span>
                <span className="text-slate-200 font-semibold">{incident.affected_user || 'N/A'}</span>
              </div>
              <div className="flex justify-between border-b border-slate-800/80 pb-2">
                <span className="text-slate-400">Risk Score:</span>
                <span className="font-mono text-amber-400 font-bold">{incident.risk_score} / 100</span>
              </div>
              <div className="flex justify-between pb-1">
                <span className="text-slate-400">Correlated Alerts:</span>
                <span className="font-mono text-cyan-400 font-semibold">{incident.alert_count}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IncidentDetailPage;
