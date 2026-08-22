import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import SeverityBadge from '../components/SeverityBadge';
import MitreBadge from '../components/MitreBadge';
import RiskScoreGauge from '../components/RiskScoreGauge';
import {
  ShieldAlert,
  Globe,
  User,
  Clock,
  CheckCircle,
  XCircle,
  MessageSquare,
  ShieldCheck,
  ArrowLeft,
  Fingerprint,
  Network,
  AlertTriangle,
  Info
} from 'lucide-react';

const AlertDetailPage = () => {
  const { id } = useParams();
  const [alert, setAlert] = useState(null);
  const [newNote, setNewNote] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchAlertDetail = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/alerts/${id}`);
      setAlert(res.data.alert);
    } catch (err) {
      console.error('Failed to fetch alert detail:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlertDetail();
  }, [id]);

  const updateStatus = async (status) => {
    try {
      await api.patch(`/alerts/${id}/status`, { status });
      fetchAlertDetail();
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const addNote = async (e) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    try {
      await api.post(`/alerts/${id}/notes`, { text: newNote });
      setNewNote('');
      fetchAlertDetail();
    } catch (err) {
      console.error('Failed to add note:', err);
    }
  };


  if (loading || !alert) {
    return <div className="p-8 text-center text-slate-400">Loading Alert ALT-{id} Telemetry...</div>;
  }

  const ipIntel = alert.ip_intelligence || {};
  const mitre = alert.mitre_details || {};

  return (
    <div className="space-y-6">
      {/* Top Header Navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/alerts" className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-slate-400">ALT-{alert.id}</span>
              <SeverityBadge severity={alert.severity} />
              <span className="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-slate-800 border border-slate-700 text-slate-300">
                {alert.status}
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-100 mt-0.5">{alert.title}</h1>
          </div>
        </div>

        {/* Status Workflow Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => updateStatus('INVESTIGATING')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${alert.status === 'INVESTIGATING' ? 'bg-amber-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
          >
            Investigating
          </button>
          <button
            onClick={() => updateStatus('RESOLVED')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 ${alert.status === 'RESOLVED' ? 'bg-emerald-600 text-white' : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'}`}
          >
            <CheckCircle className="w-3.5 h-3.5" /> Resolve
          </button>
          <button
            onClick={() => updateStatus('FALSE_POSITIVE')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 ${alert.status === 'FALSE_POSITIVE' ? 'bg-slate-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}
          >
            <XCircle className="w-3.5 h-3.5" /> False Positive
          </button>
        </div>
      </div>

      {/* Main Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Overview Card */}
          <div className="glass-panel rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">Alert Summary & Context</h3>
            <p className="text-sm text-slate-300">{alert.description}</p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <Globe className="w-3.5 h-3.5 text-blue-400" /> Source IP
                </span>
                <span className="font-mono text-sm font-semibold text-slate-100 mt-1 block">{alert.source_ip}</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <User className="w-3.5 h-3.5 text-purple-400" /> Target Account
                </span>
                <span className="text-sm font-semibold text-slate-100 mt-1 block">{alert.username || 'N/A'}</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" /> Detection Time
                </span>
                <span className="font-mono text-xs font-semibold text-slate-100 mt-1 block">
                  {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'N/A'}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-400" /> Assigned Analyst
                </span>
                <span className="text-sm font-semibold text-slate-100 mt-1 block">{alert.assigned_to || 'Unassigned'}</span>
              </div>
            </div>
          </div>

          {/* Correlation Evidence — Why This Alert? */}
          {alert.risk_factors && (
            <div className="glass-panel rounded-xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Info className="w-4 h-4 text-cyan-400" />
                Why This Alert Was Generated
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {alert.risk_factors.detection_rule && (
                  <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
                    <span className="text-[11px] text-cyan-400 font-semibold uppercase">Detection Rule</span>
                    <span className="text-sm text-slate-100 font-bold block mt-1">
                      {alert.risk_factors.detection_rule.replace(/_/g, ' ')}
                    </span>
                  </div>
                )}
                {alert.risk_factors.failed_attempts_count !== undefined && (
                  <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
                    <span className="text-[11px] text-red-400 font-semibold uppercase">Failed Attempts</span>
                    <span className="text-sm text-slate-100 font-bold block mt-1">
                      {alert.risk_factors.failed_attempts_count}
                    </span>
                  </div>
                )}
                {alert.risk_factors.unique_users !== undefined && (
                  <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/30">
                    <span className="text-[11px] text-purple-400 font-semibold uppercase">Unique Users Targeted</span>
                    <span className="text-sm text-slate-100 font-bold block mt-1">
                      {alert.risk_factors.unique_users}
                    </span>
                  </div>
                )}
                {alert.risk_factors.unique_source_ips !== undefined && (
                  <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
                    <span className="text-[11px] text-blue-400 font-semibold uppercase">Unique Source IPs</span>
                    <span className="text-sm text-slate-100 font-bold block mt-1">
                      {alert.risk_factors.unique_source_ips}
                    </span>
                  </div>
                )}
                {alert.risk_factors.time_window_mins !== undefined && (
                  <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                    <span className="text-[11px] text-amber-400 font-semibold uppercase">Time Window</span>
                    <span className="text-sm text-slate-100 font-bold block mt-1">
                      {alert.risk_factors.time_window_mins} minutes
                    </span>
                  </div>
                )}
                {alert.risk_factors.source_ip && (
                  <div className="p-3 rounded-lg bg-slate-800 border border-slate-700">
                    <span className="text-[11px] text-slate-400 font-semibold uppercase flex items-center gap-1">
                      <Network className="w-3 h-3" /> Source IP
                    </span>
                    <span className="font-mono text-sm text-slate-100 font-bold block mt-1">
                      {alert.risk_factors.source_ip}
                    </span>
                  </div>
                )}
              </div>
              {alert.risk_factors.targeted_usernames && alert.risk_factors.targeted_usernames.length > 0 && (
                <div className="mt-2">
                  <span className="text-[11px] text-slate-400 font-semibold uppercase">Targeted Usernames:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {alert.risk_factors.targeted_usernames.map((u, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-xs font-mono text-slate-300">
                        {u}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {alert.risk_factors.source_ips && alert.risk_factors.source_ips.length > 0 && (
                <div className="mt-2">
                  <span className="text-[11px] text-slate-400 font-semibold uppercase">Source IPs Involved:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {alert.risk_factors.source_ips.map((ip, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-xs font-mono text-slate-300">
                        {ip}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Event Evidence Telemetry */}
          <div className="glass-panel rounded-xl p-5">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-3">Event Telemetry Evidence ({(alert.evidence || []).length} events)</h3>
            <div className="space-y-2">
              {(alert.evidence || []).map((ev, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-900 border border-slate-800 font-mono text-xs flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                      ev.status === 'failed' ? 'bg-red-500' :
                      ev.status === 'success' ? 'bg-emerald-500' :
                      'bg-slate-500'
                    }`} />
                    <div>
                      <span className="text-blue-400 font-bold mr-2">[{(ev.event_type || 'event').toUpperCase()}]</span>
                      <span className="text-slate-300">{ev.source_ip}</span>
                      <span className="text-slate-500 mx-1">•</span>
                      <span className="text-slate-300">User: {ev.username || 'unknown'}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                      ev.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                      ev.status === 'success' ? 'bg-emerald-500/20 text-emerald-400' :
                      'bg-slate-500/20 text-slate-400'
                    }`}>
                      {ev.status || 'N/A'}
                    </span>
                    <span className="text-slate-400 text-[11px]">{ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : ''}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Defensive SOC Recommendations & Simulated Response */}
          <div className="glass-panel rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Defensive Playbook & Actionable Recommendations
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(alert.recommendations || []).map((rec, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-slate-200">{rec.action}</h4>
                    <p className="text-[11px] text-slate-400 mt-1">{rec.description}</p>
                  </div>

                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column (1 col) */}
        <div className="space-y-6">
          {/* Risk Score Gauge */}
          <RiskScoreGauge score={alert.risk_score} factors={alert.risk_factors} />

          {/* MITRE ATT&CK Card */}
          <div className="glass-panel rounded-xl p-5 space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">MITRE ATT&CK Mapping</h3>
            <div className="pt-1">
              <MitreBadge techniqueId={alert.mitre_technique_id} name={mitre.technique_name} />
              {mitre.tactic && (
                <div className="mt-2 text-xs">
                  <span className="text-slate-400">Tactic: </span>
                  <span className="text-slate-200 font-semibold">{mitre.tactic}</span>
                </div>
              )}
              {mitre.description && (
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">{mitre.description}</p>
              )}
            </div>
          </div>

          {/* IP Intelligence Card */}
          <div className="glass-panel rounded-xl p-5 space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">IP Intelligence</h3>
            <div className="text-xs space-y-1.5 pt-1">
              <div className="flex justify-between">
                <span className="text-slate-400">Country:</span>
                <span className="text-slate-200 font-semibold">{ipIntel.country || 'Private/Unknown'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Region / City:</span>
                <span className="text-slate-200 font-semibold">{ipIntel.region || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">ISP / Org:</span>
                <span className="text-slate-200 font-semibold">{ipIntel.isp || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Is Private Network:</span>
                <span className="text-slate-200 font-mono">{ipIntel.is_private ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </div>

          {/* Analyst Notes Thread */}
          <div className="glass-panel rounded-xl p-5 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <MessageSquare className="w-4 h-4 text-purple-400" /> Analyst Work Log & Notes
            </h3>

            <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar">
              {(alert.notes || []).map((n, idx) => (
                <div key={idx} className="p-2.5 rounded bg-slate-900 border border-slate-800 text-xs">
                  <div className="flex justify-between text-[10px] text-slate-400 mb-1">
                    <span className="font-semibold text-blue-400">{n.author}</span>
                    <span>{new Date(n.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-slate-300">{n.text}</p>
                </div>
              ))}
            </div>

            <form onSubmit={addNote} className="space-y-2">
              <input
                type="text"
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="Add analyst note..."
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              />
              <button type="submit" className="w-full py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold">
                Submit Note
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertDetailPage;
