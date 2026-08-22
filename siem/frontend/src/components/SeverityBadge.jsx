import React from 'react';

const SeverityBadge = ({ severity }) => {
  const sev = (severity || 'MEDIUM').toUpperCase();
  
  let colors = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  if (sev === 'CRITICAL') {
    colors = 'bg-rose-500/15 text-rose-400 border-rose-500/40 animate-pulse';
  } else if (sev === 'HIGH') {
    colors = 'bg-orange-500/15 text-orange-400 border-orange-500/40';
  } else if (sev === 'LOW') {
    colors = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  } else if (sev === 'INFO') {
    colors = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${colors}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
      {sev}
    </span>
  );
};

export default SeverityBadge;
