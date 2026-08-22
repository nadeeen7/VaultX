import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { socket } from '../services/socket';
import MetricCard from '../components/MetricCard';
import SeverityBadge from '../components/SeverityBadge';
import MitreBadge from '../components/MitreBadge';
import {
  Activity,
  ShieldAlert,
  AlertOctagon,
  Flame,
  GitPullRequest,
  Cpu,
  ArrowRight,
  RefreshCw,
  Globe,
  Target,
  CheckCircle
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  CartesianGrid,
  Legend
} from 'recharts';

const SEVERITY_COLORS = {
  CRITICAL: '#EF4444',
  HIGH: '#F97316',
  MEDIUM: '#F59E0B',
  LOW: '#10B981'
};

const BAR_COLORS = ['#3B82F6', '#8B5CF6', '#06B6D4', '#10B981', '#F59E0B'];

const TOOLTIP_STYLE = {
  backgroundColor: '#0F172A',
  border: '1px solid #334155',
  borderRadius: '8px',
  color: '#F8FAFC',
  fontSize: '11px',
  boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={TOOLTIP_STYLE} className="px-3 py-2">
      <p className="text-xs font-semibold text-slate-300 mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="text-xs" style={{ color: entry.color }}>
          {entry.name}: <span className="font-bold">{entry.value}</span>
        </p>
      ))}
    </div>
  );
};

const DashboardPage = () => {
  const [metrics, setMetrics] = useState(null);
  const [charts, setCharts] = useState(null);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshed, setRefreshed] = useState(false);

  const fetchDashboardData = async () => {
    try {
      const res = await api.get('/analytics/dashboard');
      setMetrics(res.data.metrics);
      setCharts(res.data.charts);
      setRecentAlerts(res.data.recent_alerts);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    if (refreshing) return;
    setRefreshing(true);
    setRefreshed(false);
    try {
      await fetchDashboardData();
      setRefreshed(true);
      setTimeout(() => setRefreshed(false), 2000);
    } catch (err) {
      console.error('[Dashboard] Refresh failed:', err);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    const handleNewAlert = (newAlert) => {
      setRecentAlerts((prev) => [newAlert, ...prev.slice(0, 9)]);
      setMetrics((prev) => prev ? ({
        ...prev,
        total_alerts: prev.total_alerts + 1,
        critical_alerts: newAlert.severity === 'CRITICAL' ? prev.critical_alerts + 1 : prev.critical_alerts,
        high_alerts: newAlert.severity === 'HIGH' ? prev.high_alerts + 1 : prev.high_alerts
      }) : null);
    };

    const handleNewEvent = () => {
      setMetrics((prev) => prev ? ({ ...prev, total_events: prev.total_events + 1 }) : null);
    };

    socket.on('new_alert', handleNewAlert);
    socket.on('new_event', handleNewEvent);

    return () => {
      socket.off('new_alert', handleNewAlert);
      socket.off('new_event', handleNewEvent);
    };
  }, []);

  const totalSeverity = (charts?.severity_distribution || []).reduce((sum, e) => sum + e.value, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin mr-2" />
        <span>Loading SOC Dashboard Telemetry...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Security Operations Center</h1>
          <p className="text-xs text-slate-400">Real-time threat monitoring and event telemetry</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''} ${refreshed ? 'text-emerald-400' : ''}`} />
          <span className={refreshed ? 'text-emerald-400' : ''}>{refreshing ? 'Refreshing...' : refreshed ? 'Updated!' : 'Refresh Data'}</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard title="Total Events" value={metrics?.total_events} icon={Activity} color="blue" to="/events" />
        <MetricCard title="Total Alerts" value={metrics?.total_alerts} icon={ShieldAlert} color="purple" to="/alerts" />
        <MetricCard title="Critical Alerts" value={metrics?.critical_alerts} icon={AlertOctagon} color="rose" to="/alerts?severity=CRITICAL" />
        <MetricCard title="High Alerts" value={metrics?.high_alerts} icon={Flame} color="amber" to="/alerts?severity=HIGH" />
        <MetricCard title="Open Incidents" value={metrics?.open_incidents} icon={GitPullRequest} color="cyan" to="/incidents" />
        <MetricCard title="Anomalies" value={metrics?.total_anomalies} icon={Cpu} color="emerald" to="/analytics" />
      </div>

      {/* Row 1: Timeline + Severity Donut */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline Chart — stacked area for clarity */}
        <div className="glass-panel rounded-xl p-5 lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-200 mb-1">Events & Alerts Over Time (24h)</h3>
          <p className="text-[10px] text-slate-500 mb-4">Hourly distribution of ingested events and triggered alerts</p>
          <div className="h-64" style={{ background: 'transparent' }}>
            <ResponsiveContainer width="100%" height="100%" style={{ background: 'transparent' }}>
              <AreaChart data={charts?.events_over_time || []} style={{ background: 'transparent' }}>
                <defs>
                  <linearGradient id="gradEvents" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#3B82F6" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="gradAlerts" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#EF4444" stopOpacity={0.45} />
                    <stop offset="100%" stopColor="#EF4444" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis
                  dataKey="hour"
                  stroke="#475569"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="#475569"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  width={30}
                />
                <Tooltip content={<CustomTooltip />} wrapperStyle={{ zIndex: 10 }} />
                <Legend
                  iconType="circle"
                  iconSize={8}
                  wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }}
                />
                <Area
                  type="monotone"
                  dataKey="events"
                  name="Events"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  fill="url(#gradEvents)"
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 2 }}
                />
                <Area
                  type="monotone"
                  dataKey="alerts"
                  name="Alerts"
                  stroke="#EF4444"
                  strokeWidth={2}
                  fill="url(#gradAlerts)"
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Donut with center label */}
        <div className="glass-panel rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-1">Alerts by Severity</h3>
          <p className="text-[10px] text-slate-500 mb-2">Distribution of alert severity levels</p>
          <div className="h-64 relative flex items-center justify-center" style={{ background: 'transparent' }}>
            <ResponsiveContainer width="100%" height="100%" style={{ background: 'transparent' }}>
              <PieChart style={{ background: 'transparent' }}>
                <Pie
                  data={charts?.severity_distribution || []}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                >
                  {(charts?.severity_distribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={SEVERITY_COLORS[entry.name] || '#64748B'} />
                  ))}
                </Pie>              <Tooltip contentStyle={TOOLTIP_STYLE}
                  formatter={(value, name) => [`${value} (${((value / Math.max(totalSeverity, 1)) * 100).toFixed(0)}%)`, name]}
                />
              </PieChart>
            </ResponsiveContainer>
            {/* Center label */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-bold text-slate-100">{totalSeverity}</span>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider">Total</span>
            </div>
          </div>
          {/* Legend */}
          <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 mt-2">
            {(charts?.severity_distribution || []).filter(e => e.value > 0).map((entry) => (
              <div key={entry.name} className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: SEVERITY_COLORS[entry.name] }} />
                <span className="text-[10px] text-slate-400">{entry.name}</span>
                <span className="text-[10px] font-bold text-slate-300">{entry.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 2: Top IPs, MITRE Techniques, Geo Distribution, Top Attack Types */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Source IPs */}
        <div className="glass-panel rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-1">Top Attacker Source IPs</h3>
          <p className="text-[10px] text-slate-500 mb-4">Source IPs with the most generated alerts</p>
          <div className="h-48" style={{ background: 'transparent' }}>
            {(charts?.top_source_ips || []).length > 0 ? (
              <ResponsiveContainer width="100%" height="100%" style={{ background: 'transparent' }}>
                <BarChart data={charts.top_source_ips} layout="vertical" margin={{ left: 10 }} style={{ background: 'transparent' }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" horizontal={false} />
                  <XAxis type="number" stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis
                    dataKey="ip"
                    type="category"
                    stroke="#475569"
                    fontSize={10}
                    tickLine={false}
                    axisLine={false}
                    width={100}
                    tickFormatter={(v) => v.length > 15 ? v.slice(0, 12) + '…' : v}
                  />
                  <Tooltip content={<CustomTooltip />} contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="count" name="Alerts" radius={[0, 6, 6, 0]} barSize={28}>
                    {(charts.top_source_ips || []).map((_, i) => (
                      <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-500 text-xs">No attacker IPs recorded yet</div>
            )}
          </div>
        </div>

        {/* MITRE ATT&CK Breakdown */}
        <div className="glass-panel rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-1">Top Triggered MITRE Techniques</h3>
          <p className="text-[10px] text-slate-500 mb-4">Most frequently triggered attack technique IDs</p>
          <div className="h-48" style={{ background: 'transparent' }}>
            {(charts?.mitre_distribution || []).length > 0 ? (
              <ResponsiveContainer width="100%" height="100%" style={{ background: 'transparent' }}>
                <BarChart data={charts.mitre_distribution} style={{ background: 'transparent' }} margin={{ left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                  <XAxis
                    dataKey="technique_id"
                    stroke="#475569"
                    fontSize={10}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis stroke="#475569" fontSize={10} tickLine={false} axisLine={false} width={30} />
                  <Tooltip content={<CustomTooltip />} contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="count" name="Alerts" radius={[6, 6, 0, 0]} barSize={40}>
                    {(charts.mitre_distribution || []).map((_, i) => (
                      <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-500 text-xs">No MITRE techniques triggered yet</div>
            )}
          </div>
        </div>
      </div>

      {/* Row 3: Geographic Distribution + Top Attack Types */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Geographic Distribution */}
        <div className="glass-panel rounded-xl p-5">
          <div className="flex items-center gap-2 mb-1">
            <Globe className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-200">Geographic Distribution</h3>
          </div>
          <p className="text-[10px] text-slate-500 mb-4">Source countries of ingested IP addresses</p>
          <div className="h-48" style={{ background: 'transparent' }}>
            {(charts?.geo_distribution || []).length > 0 ? (
              <ResponsiveContainer width="100%" height="100%" style={{ background: 'transparent' }}>
                <BarChart data={charts.geo_distribution} style={{ background: 'transparent' }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                  <XAxis dataKey="country" stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#475569" fontSize={10} tickLine={false} axisLine={false} width={30} />
                  <Tooltip content={<CustomTooltip />} contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="count" name="IPs" radius={[6, 6, 0, 0]} barSize={40}>
                    {(charts.geo_distribution || []).map((_, i) => (
                      <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-500 text-xs">No geolocation data available yet</div>
            )}
          </div>
        </div>

        {/* Top Attack Types */}
        <div className="glass-panel rounded-xl p-5">
          <div className="flex items-center gap-2 mb-1">
            <Target className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-slate-200">Top Attack Types</h3>
          </div>
          <p className="text-[10px] text-slate-500 mb-4">Most frequently triggered alert titles</p>
          <div className="h-48" style={{ background: 'transparent' }}>
            {(charts?.top_attack_types || []).length > 0 ? (
              <ResponsiveContainer width="100%" height="100%" style={{ background: 'transparent' }}>
                <BarChart data={charts.top_attack_types} layout="vertical" margin={{ left: 10 }} style={{ background: 'transparent' }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" horizontal={false} />
                  <XAxis type="number" stroke="#475569" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis
                    dataKey="title"
                    type="category"
                    stroke="#475569"
                    fontSize={9}
                    tickLine={false}
                    axisLine={false}
                    width={160}
                    tickFormatter={(v) => v.length > 22 ? v.slice(0, 20) + '…' : v}
                  />
                  <Tooltip content={<CustomTooltip />} contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="count" name="Alerts" radius={[0, 6, 6, 0]} barSize={22}>
                    {(charts.top_attack_types || []).map((_, i) => (
                      <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-500 text-xs">No attack types recorded yet</div>
            )}
          </div>
        </div>
      </div>

      {/* Real-time Live Alerts Table */}
      <div className="glass-panel rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <h3 className="text-sm font-bold text-slate-100">Live Security Alerts Stream</h3>
          </div>
          <Link to="/alerts" className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-semibold">
            View All Alerts <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-3">Alert ID</th>
                <th className="p-3">Severity</th>
                <th className="p-3">Title</th>
                <th className="p-3">Source IP</th>
                <th className="p-3">User</th>
                <th className="p-3">MITRE</th>
                <th className="p-3">Risk Score</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {recentAlerts.map((alert) => (
                <tr key={alert.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-3 font-mono font-semibold text-slate-300">ALT-{alert.id}</td>
                  <td className="p-3"><SeverityBadge severity={alert.severity} /></td>
                  <td className="p-3 max-w-xs">
                    <div className="font-medium text-slate-200 truncate">{alert.title}</div>
                    {alert.risk_factors?.detection_rule && (
                      <span className="text-[9px] font-mono text-cyan-400 uppercase">
                        {alert.risk_factors.detection_rule.replace(/_/g, ' ')}
                      </span>
                    )}
                  </td>
                  <td className="p-3 font-mono text-slate-300">{alert.source_ip}</td>
                  <td className="p-3 text-slate-300">{alert.username || 'N/A'}</td>
                  <td className="p-3"><MitreBadge techniqueId={alert.mitre_technique_id} /></td>
                  <td className="p-3 font-mono font-bold text-amber-400">{alert.risk_score}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-slate-800 border border-slate-700 text-slate-300">
                      {alert.status}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <Link to={`/alerts/${alert.id}`} className="text-blue-400 hover:underline font-semibold">
                      Investigate
                    </Link>
                  </td>
                </tr>
              ))}
              {recentAlerts.length === 0 && (
                <tr>
                  <td colSpan={9} className="p-8 text-center text-slate-500">
                    No alerts yet. Events will appear here once detected.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
