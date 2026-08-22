import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';

const RiskScoreGauge = ({ score, factors }) => {
  const numericScore = parseFloat(score || 0);

  let scoreColor = 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
  if (numericScore >= 80) scoreColor = 'text-rose-400 border-rose-500/40 bg-rose-500/15';
  else if (numericScore >= 50) scoreColor = 'text-amber-400 border-amber-500/30 bg-amber-500/10';

  const breakdownList = factors?.breakdown || [];

  return (
    <div className="bg-slate-900/60 rounded-xl p-4 border border-slate-800">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          Transparent Risk Score
        </span>
        <div className={`px-3 py-1 rounded-lg border font-mono text-lg font-bold ${scoreColor}`}>
          {numericScore} / 100
        </div>
      </div>

      {/* Visual Bar */}
      <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden mb-4">
        <div 
          className={`h-full transition-all duration-500 ${
            numericScore >= 80 ? 'bg-gradient-to-r from-amber-500 to-rose-500' :
            numericScore >= 50 ? 'bg-gradient-to-r from-blue-500 to-amber-500' :
            'bg-gradient-to-r from-cyan-500 to-emerald-500'
          }`}
          style={{ width: `${Math.min(100, Math.max(5, numericScore))}%` }}
        />
      </div>

      {/* Factor Reasoning Breakdown */}
      {breakdownList.length > 0 && (
        <div className="space-y-2 mt-3 pt-3 border-t border-slate-800/80">
          <p className="text-xs font-medium text-slate-300 flex items-center gap-1">
            <Info className="w-3.5 h-3.5 text-blue-400" />
            Score Rationale & Breakdown:
          </p>
          <div className="space-y-1.5">
            {breakdownList.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs bg-slate-800/40 px-2.5 py-1.5 rounded border border-slate-800">
                <span className="text-slate-300 font-medium">{item.factor}</span>
                <span className="font-mono text-emerald-400 font-semibold">+{item.points} pts</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskScoreGauge;
