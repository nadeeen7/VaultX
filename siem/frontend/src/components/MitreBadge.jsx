import React from 'react';
import { ShieldAlert } from 'lucide-react';

const MitreBadge = ({ techniqueId, name }) => {
  if (!techniqueId) return <span className="text-slate-500 text-xs">Unmapped</span>;

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-blue-500/10 border border-blue-500/30 text-blue-400 font-mono text-xs">
      <ShieldAlert className="w-3.5 h-3.5" />
      <span>{techniqueId}</span>
      {name && <span className="text-slate-400 font-sans border-l border-slate-700 pl-1.5 truncate max-w-[120px]">{name}</span>}
    </div>
  );
};

export default MitreBadge;
