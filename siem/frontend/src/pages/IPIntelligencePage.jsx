import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import SeverityBadge from '../components/SeverityBadge';
import {
  Globe, Search, Shield, Server, MapPin, Users, Activity,
  AlertTriangle, Clock, ArrowRight, RefreshCw, ExternalLink,
  Wifi, Ban, CheckCircle, XCircle
} from 'lucide-react';

const IPIntelligencePage = () => {
  const [searchIp, setSearchIp] = useState('');
  const [ipData, setIpData] = useState(null);
  const [cachedIps, setCachedIps] = useState([]);
  const [ipEvents, setIpEvents] = useState([]);
  const [ipAlerts, setIpAlerts] = useState([]);
  const [geoStats, setGeoStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchIpDetails = async (ip) => {
    if (!ip) return;
    setLoading(true);
    try {
      const res = await api.get(`/ip-intelligence/${ip}`);
      setIpData(res.data.ip_intelligence);
      // Fetch events and alerts in parallel
      const [eventsRes, alertsRes] = await Promise.all([
        api.get(`/ip-intelligence/${ip}/events?per_page=15`),
        api.get(`/ip-intelligence/${ip}/alerts?per_page=15`)
      ]);
      setIpEvents(eventsRes.data.events);
      setIpAlerts(alertsRes.data.alerts);
    } catch (err) {
      console.error('Failed to fetch IP intel:', err);
      setIpData(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchCachedIps = async () => {
    try {
      const res = await api.get('/ip-intelligence');
      setCachedIps(res.data.ips);
    } catch (err) {
      console.error('Failed to fetch cached IPs:', err);
    }
  };

  const fetchGeoStats = async () => {
    try {
      const res = await api.get('/ip-intelligence/geo-stats');
      setGeoStats(res.data);
    } catch (err) {
      console.error('Failed to fetch geo stats:', err);
    }
  };

  useEffect(() => {
    fetchCachedIps();
    fetchGeoStats();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchIp.trim()) {
      fetchIpDetails(searchIp.trim());
      setActiveTab('overview');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">IP Intelligence Portal</h1>
          <p className="text-xs text-slate-400">
            IP geolocation, ISP intelligence, and historical threat telemetry — based on approximate IP geolocation data
          </p>
        </div>
        <button
          onClick={() => { fetchCachedIps(); fetchGeoStats(); }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* Search Input */}
      <form onSubmit={handleSearch} className="glass-panel rounded-xl p-4 flex gap-3">
        <div className="relative flex-1">
          <Globe className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search IP Address (e.g. 192.168.1.100 or 10.0.0.1)..."
            value={searchIp}
            onChange={(e) => setSearchIp(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500 font-mono"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
        >
          {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
          Lookup IP
        </button>
      </form>

      {/* Result Display */}
      {ipData && (
        <>
          {/* IP Header Card */}
          <div className="glass-panel rounded-xl p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-4">
                <div className={`p-4 rounded-xl border ${
                  ipData.is_private
                    ? 'bg-slate-800 border-slate-700 text-slate-400'
                    : ipData.country === 'Unavailable'
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                    : 'bg-blue-500/10 border-blue-500/30 text-blue-400'
                }`}>
                  <Globe className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="font-mono text-xl font-bold text-slate-100">{ipData.ip_address}</h2>
                  <p className="text-sm text-slate-400">
                    {ipData.city !== 'N/A' ? `${ipData.city}, ` : ''}{ipData.region !== 'N/A' ? `${ipData.region}, ` : ''}{ipData.country}
                  </p>
                  {ipData.latitude && ipData.longitude && (
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Approx. {ipData.latitude.toFixed(4)}, {ipData.longitude.toFixed(4)}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {ipData.is_private && (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1">
                    <Ban className="w-3 h-3" /> Private Network
                  </span>
                )}
                {!ipData.is_private && ipData.country !== 'Unavailable' && (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 flex items-center gap-1">
                    <Globe className="w-3 h-3" /> Public Internet
                  </span>
                )}
                {ipData.country === 'Unavailable' && (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> Lookup Unavailable
                  </span>
                )}
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mt-4">
              {[
                { label: 'Events', value: ipData.event_count || 0, color: 'text-blue-400' },
                { label: 'Alerts', value: ipData.alert_count || 0, color: 'text-rose-400' },
                { label: 'Failed Logins', value: ipData.failed_logins || 0, color: 'text-amber-400' },
                { label: 'Successful', value: ipData.successful_logins || 0, color: 'text-emerald-400' },
                { label: 'Affected Accounts', value: ipData.affected_accounts || 0, color: 'text-purple-400' },
                { label: 'First Seen', value: ipData.first_seen ? new Date(ipData.first_seen).toLocaleDateString() : 'N/A', color: 'text-slate-300', small: true },
              ].map((stat) => (
                <div key={stat.label} className="text-center">
                  <p className={`font-mono font-bold ${stat.color} ${stat.small ? 'text-sm' : 'text-lg'}`}>{stat.value}</p>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 bg-slate-900 rounded-lg p-1 w-fit">
            {['overview', 'activity', 'users', 'alerts'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-1.5 rounded-md text-xs font-semibold uppercase transition-colors ${
                  activeTab === tab
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* IP Details */}
              <div className="glass-panel rounded-xl p-5 space-y-3">
                <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <Server className="w-4 h-4 text-blue-400" /> Network Intelligence
                </h3>
                {[
                  { label: 'ISP', value: ipData.isp },
                  { label: 'Organization', value: ipData.org },
                  { label: 'ASN', value: ipData.asn },
                  { label: 'Timezone', value: ipData.timezone },
                  { label: 'Country Code', value: ipData.country_code },
                  { label: 'Region', value: ipData.region },
                  { label: 'City', value: ipData.city },
                ].map((item) => (
                  <div key={item.label} className="flex justify-between items-center py-1.5 border-b border-slate-800/80">
                    <span className="text-xs text-slate-400">{item.label}</span>
                    <span className="text-xs font-mono font-semibold text-slate-200">{item.value || 'N/A'}</span>
                  </div>
                ))}
              </div>

              {/* Associated Users */}
              <div className="glass-panel rounded-xl p-5 space-y-3">
                <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <Users className="w-4 h-4 text-purple-400" /> Associated Users ({ipData.associated_users?.length || 0})
                </h3>
                {(ipData.associated_users || []).length > 0 ? (
                  <div className="space-y-2">
                    {ipData.associated_users.map((user) => (
                      <div key={user.username} className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
                        <div>
                          <span className="text-sm font-semibold text-slate-200">{user.username}</span>
                          <div className="flex gap-3 mt-1 text-[10px] font-mono">
                            <span className="text-blue-400">{user.event_count} events</span>
                            <span className="text-amber-400">{user.failed_logins} failed</span>
                            <span className="text-emerald-400">{user.successful_logins} success</span>
                          </div>
                        </div>
                        <div className="text-right text-[10px] text-slate-500">
                          {user.last_seen && <p>Last: {new Date(user.last_seen).toLocaleString()}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 text-center py-4">No associated users found</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'activity' && (
            <div className="glass-panel rounded-xl p-5">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" /> Security Event History
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="p-2">Time</th>
                      <th className="p-2">Event</th>
                      <th className="p-2">Status</th>
                      <th className="p-2">User</th>
                      <th className="p-2">Endpoint</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {ipEvents.map((evt) => (
                      <tr key={evt.id} className="hover:bg-slate-800/30">
                        <td className="p-2 font-mono text-slate-400">{evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : '—'}</td>
                        <td className="p-2 font-mono text-slate-200">{evt.event_type}</td>
                        <td className="p-2">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                            evt.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' :
                            evt.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                            'bg-slate-700 text-slate-400'
                          }`}>{evt.status}</span>
                        </td>
                        <td className="p-2 text-slate-300">{evt.username || '—'}</td>
                        <td className="p-2 font-mono text-slate-500 text-[10px]">{evt.endpoint || '—'}</td>
                      </tr>
                    ))}
                    {ipEvents.length === 0 && (
                      <tr><td colSpan={5} className="p-8 text-center text-slate-500">No events recorded for this IP</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'users' && (
            <div className="glass-panel rounded-xl p-5">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Users className="w-4 h-4 text-purple-400" /> User Activity from This IP
              </h3>
              {(ipData.associated_users || []).length > 0 ? (
                <div className="space-y-3">
                  {ipData.associated_users.map((user) => (
                    <div key={user.username} className="p-4 rounded-lg bg-slate-900 border border-slate-800">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-slate-100">{user.username}</span>
                        <Link to={`/alerts?source_ip=${ipData.ip_address}`} className="text-blue-400 text-xs hover:underline flex items-center gap-1">
                          View Alerts <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                        <div>
                          <span className="text-slate-500 block">Events</span>
                          <span className="font-mono font-bold text-blue-400">{user.event_count}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Failed Logins</span>
                          <span className="font-mono font-bold text-amber-400">{user.failed_logins}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Successful</span>
                          <span className="font-mono font-bold text-emerald-400">{user.successful_logins}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">First Seen</span>
                          <span className="font-mono text-slate-300">{user.first_seen ? new Date(user.first_seen).toLocaleDateString() : 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Last Activity</span>
                          <span className="font-mono text-slate-300">{user.last_seen ? new Date(user.last_seen).toLocaleString() : 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 text-center py-8">No user activity found for this IP</p>
              )}
            </div>
          )}

          {activeTab === 'alerts' && (
            <div className="glass-panel rounded-xl p-5">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" /> Alerts from This IP ({ipAlerts.length})
              </h3>
              {ipAlerts.length > 0 ? (
                <div className="space-y-2">
                  {ipAlerts.map((alert) => (
                    <Link
                      key={alert.id}
                      to={`/alerts/${alert.id}`}
                      className="block p-3 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800/60 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <SeverityBadge severity={alert.severity} />
                          <div>
                            <span className="text-sm font-semibold text-slate-200">{alert.title}</span>
                            <p className="text-[11px] text-slate-400 mt-0.5">{alert.description?.slice(0, 100)}...</p>
                          </div>
                        </div>
                        <span className="font-mono text-xs text-slate-500">
                          {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : ''}
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 text-center py-8">No alerts triggered from this IP</p>
              )}
            </div>
          )}
        </>
      )}

      {/* Bottom Section: Geo Stats + Cached IPs */}
      {!ipData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Geographic Statistics */}
          {geoStats && (
            <div className="glass-panel rounded-xl p-5 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <MapPin className="w-4 h-4 text-cyan-400" /> Geographic Intelligence Summary
              </h3>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                  <p className="font-mono text-lg font-bold text-blue-400">{geoStats.total_ips || 0}</p>
                  <p className="text-[10px] text-slate-500 uppercase">Total IPs</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                  <p className="font-mono text-lg font-bold text-emerald-400">{geoStats.public_ips || 0}</p>
                  <p className="text-[10px] text-slate-500 uppercase">Public</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                  <p className="font-mono text-lg font-bold text-slate-400">{geoStats.private_ips || 0}</p>
                  <p className="text-[10px] text-slate-500 uppercase">Private</p>
                </div>
              </div>

              {geoStats.top_countries?.length > 0 && (
                <div>
                  <p className="text-[10px] text-slate-500 uppercase mb-2">Top Countries</p>
                  <div className="space-y-1.5">
                    {geoStats.top_countries.map((c) => (
                      <div key={c.country} className="flex items-center justify-between text-xs">
                        <span className="text-slate-300">{c.country}</span>
                        <span className="font-mono font-bold text-blue-400">{c.count} IPs</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {geoStats.top_cities?.length > 0 && (
                <div>
                  <p className="text-[10px] text-slate-500 uppercase mb-2">Top Cities</p>
                  <div className="space-y-1.5">
                    {geoStats.top_cities.map((c) => (
                      <div key={`${c.city}-${c.country}`} className="flex items-center justify-between text-xs">
                        <span className="text-slate-300">{c.city}, {c.country}</span>
                        <span className="font-mono font-bold text-cyan-400">{c.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Cached IPs List */}
          <div className="glass-panel rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-400" /> Recently Resolved IPs ({cachedIps.length})
            </h3>
            <p className="text-[10px] text-slate-500">Click any IP to view its full intelligence profile</p>
            <div className="space-y-2 max-h-96 overflow-y-auto custom-scrollbar">
              {cachedIps.map((item) => (
                <div
                  key={item.id}
                  onClick={() => { setSearchIp(item.ip_address); fetchIpDetails(item.ip_address); setActiveTab('overview'); }}
                  className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs flex items-center justify-between cursor-pointer hover:bg-slate-800/60 transition-colors"
                >
                  <div>
                    <span className="font-mono font-semibold text-slate-300">{item.ip_address}</span>
                    <p className="text-[10px] text-slate-500">{item.city !== 'N/A' ? item.city : ''} {item.country}</p>
                  </div>
                  <div className="text-right">
                    {item.event_count > 0 && (
                      <span className="text-[10px] text-blue-400 block">{item.event_count} events</span>
                    )}
                    {item.alert_count > 0 && (
                      <span className="text-[10px] text-rose-400 block">{item.alert_count} alerts</span>
                    )}
                  </div>
                </div>
              ))}
              {cachedIps.length === 0 && (
                <p className="text-xs text-slate-500 text-center py-8">No IPs cached yet. Events will populate this list.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Privacy Notice */}
      <div className="glass-panel rounded-xl p-4 flex items-start gap-3 border border-amber-500/20">
        <Shield className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-slate-400">
          <p className="font-semibold text-amber-400 mb-1">IP Geolocation Accuracy Notice</p>
          <p>IP geolocation provides an <strong className="text-slate-300">approximate</strong> location associated with an IP address. It does <strong className="text-slate-300">not</strong> identify the exact physical location of a person or device. Results may be affected by VPNs, proxies, corporate networks, cloud providers, and mobile carriers. Private/local IP addresses (127.0.0.1, 10.x.x.x, 192.168.x.x) do not have public geolocation data.</p>
        </div>
      </div>
    </div>
  );
};

export default IPIntelligencePage;
