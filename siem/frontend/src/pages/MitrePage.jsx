import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Grid, ShieldAlert, CheckCircle2 } from 'lucide-react';

const MitrePage = () => {
  const [techniques, setTechniques] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchMitreData = async () => {
    setLoading(true);
    try {
      const res = await api.get('/mitre');
      setTechniques(res.data.techniques);
    } catch (err) {
      console.error('Failed to fetch MITRE matrix:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMitreData();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">MITRE ATT&CK Matrix Mapping</h1>
        <p className="text-xs text-slate-400">Tactics, techniques, and real-time detection telemetry heatmap</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {techniques.map((tech) => (
          <div
            key={tech.technique_id}
            className={`glass-panel rounded-xl p-5 border transition-all ${
              tech.detection_count > 0 ? 'border-rose-500/40 bg-rose-500/5' : 'border-slate-800'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/30 text-blue-400">
                {tech.technique_id}
              </span>
              {tech.detection_count > 0 ? (
                <span className="px-2 py-0.5 rounded-full text-[10px] uppercase font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30 flex items-center gap-1 animate-pulse">
                  <ShieldAlert className="w-3 h-3" />
                  {tech.detection_count} Detections Triggered
                </span>
              ) : (
                <span className="text-[10px] text-slate-500 font-mono">0 Detections</span>
              )}
            </div>

            <h3 className="font-bold text-slate-100 text-sm mb-1">{tech.technique_name}</h3>
            <span className="inline-block text-[11px] font-mono text-purple-400 mb-2">Tactic: {tech.tactic}</span>

            <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed mb-3">{tech.description}</p>

            <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 font-mono">
              Platform: {tech.platform}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MitrePage;
