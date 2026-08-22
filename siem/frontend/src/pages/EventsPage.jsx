import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { socket } from '../services/socket';
import { Activity, Search, Filter, RefreshCw, Terminal } from 'lucide-react';

const EventsPage = () => {
  const [events, setEvents] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchIp, setSearchIp] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const res = await api.get('/events', {
        params: {
          page,
          per_page: 20,
          source_ip: searchIp || undefined,
          event_type: eventTypeFilter || undefined
        }
      });
      setEvents(res.data.events);
      setTotalPages(res.data.pages);
    } catch (err) {
      console.error('Failed to fetch events:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();

    const handleNewEvent = (newEvt) => {
      setEvents((prev) => [newEvt, ...prev.slice(0, 19)]);
    };
    socket.on('new_event', handleNewEvent);
    return () => socket.off('new_event', handleNewEvent);
  }, [page, searchIp, eventTypeFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Security Events Explorer</h1>
          <p className="text-xs text-slate-400">Raw log telemetry ingested from SecureBank Lab</p>
        </div>
        <button
          onClick={fetchEvents}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-panel rounded-xl p-4 flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by Source IP..."
            value={searchIp}
            onChange={(e) => setSearchIp(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Event Types</option>
            <option value="login_success">login_success</option>
            <option value="login_failed">login_failed</option>
            <option value="admin_access_denied">admin_access_denied</option>
            <option value="api_request_burst">api_request_burst</option>
          </select>
        </div>
      </div>

      {/* Events Table & Detail Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass-panel rounded-xl p-5 lg:col-span-2 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-3">Time</th>
                <th className="p-3">Event Type</th>
                <th className="p-3">Status</th>
                <th className="p-3">Source IP</th>
                <th className="p-3">User</th>
                <th className="p-3 text-right">Raw</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {events.map((evt) => (
                <tr
                  key={evt.id}
                  onClick={() => setSelectedEvent(evt)}
                  className={`cursor-pointer transition-colors ${selectedEvent?.id === evt.id ? 'bg-blue-600/15 border-l-2 border-blue-500' : 'hover:bg-slate-800/40'}`}
                >
                  <td className="p-3 font-mono text-slate-400 whitespace-nowrap">
                    {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : 'N/A'}
                  </td>
                  <td className="p-3 font-mono font-semibold text-slate-200">{evt.event_type}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-semibold ${
                      evt.status === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
                      evt.status === 'failed' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' :
                      'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}>
                      {evt.status || 'info'}
                    </span>
                  </td>
                  <td className="p-3 font-mono text-slate-300">{evt.source_ip}</td>
                  <td className="p-3 text-slate-300">{evt.username || 'N/A'}</td>
                  <td className="p-3 text-right font-mono text-blue-400">View JSON</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-800 text-xs">
            <span className="text-slate-400">Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 rounded bg-slate-800 text-slate-300 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 rounded bg-slate-800 text-slate-300 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </div>

        {/* JSON Detail Drawer */}
        <div className="glass-panel rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-800">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-slate-200">Raw Event Payload Inspector</h3>
          </div>

          {selectedEvent ? (
            <div className="space-y-3 font-mono text-xs">
              <div>
                <span className="text-slate-500">Event ID:</span> <span className="text-slate-200">{selectedEvent.id}</span>
              </div>
              <div>
                <span className="text-slate-500">External ID:</span> <span className="text-slate-300">{selectedEvent.external_id}</span>
              </div>
              <div>
                <span className="text-slate-500">Source App:</span> <span className="text-blue-400">{selectedEvent.source_app}</span>
              </div>
              <div className="pt-2">
                <span className="text-slate-400 font-sans font-semibold block mb-1">Details JSON:</span>
                <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-cyan-300 overflow-x-auto text-[11px]">
                  {JSON.stringify(selectedEvent.details, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400 py-8 text-center">Click any event row on the left to inspect raw payload.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default EventsPage;
