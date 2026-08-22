import React, { useState, useEffect } from 'react';
import api from '../services/api';
import SeverityBadge from '../components/SeverityBadge';
import { Clock, RefreshCw, ShieldAlert, Activity } from 'lucide-react';

const TimelinePage = () => {
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTimeline = async () => {
    setLoading(true);
    try {
      const res = await api.get('/incidents/timeline');
      setTimeline(res.data.timeline);
    } catch (err) {
      console.error('Failed to fetch timeline:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Global Attack Timeline</h1>
          <p className="text-xs text-slate-400">Chronological reconstruction of security events and threat detections</p>
        </div>
        <button
          onClick={fetchTimeline}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Timeline</span>
        </button>
      </div>

      <div className="glass-panel rounded-xl p-6">
        {timeline.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-xs">
            No threat timeline events recorded yet. Events will appear here as they are detected from real bank activity.
          </div>
        ) : (
          <div className="relative pl-8 space-y-6 before:absolute before:left-3.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
            {timeline.map((item, idx) => (
              <div key={idx} className="relative flex items-start gap-4">
                <div className={`absolute -left-8 top-1.5 w-4 h-4 rounded-full border-2 bg-slate-900 flex items-center justify-center ${
                  item.type === 'ALERT' ? 'border-rose-500' : 'border-blue-400'
                }`}>
                  {item.type === 'ALERT' ? (
                    <ShieldAlert className="w-2.5 h-2.5 text-rose-400" />
                  ) : (
                    <Activity className="w-2.5 h-2.5 text-blue-400" />
                  )}
                </div>

                <div className="glass-panel rounded-xl p-4 w-full border border-slate-800 text-xs hover:border-slate-700 transition-all">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-100 text-sm">{item.event_title}</span>
                      {item.severity && <SeverityBadge severity={item.severity} />}
                    </div>
                    <span className="font-mono text-xs text-slate-400">
                      {item.timestamp ? new Date(item.timestamp).toLocaleString() : ''}
                    </span>
                  </div>

                  <p className="text-slate-300 text-xs mb-3">{item.details}</p>

                  <div className="flex flex-wrap items-center gap-4 font-mono text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
                    <div>
                      <span className="text-slate-500">Source IP:</span> <span className="text-slate-200">{item.source_ip}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Target User:</span> <span className="text-slate-200">{item.user}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Detection Context:</span> <span className="text-cyan-400">{item.detection}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TimelinePage;
