import React from 'react';
import { Link } from 'react-router-dom';

const MetricCard = ({ title, value, icon: Icon, color = 'blue', subtitle, to }) => {
  const colorStyles = {
    blue: 'border-blue-500/30 text-blue-400 bg-blue-500/10',
    rose: 'border-rose-500/40 text-rose-400 bg-rose-500/15',
    amber: 'border-amber-500/30 text-amber-400 bg-amber-500/10',
    emerald: 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10',
    purple: 'border-purple-500/30 text-purple-400 bg-purple-500/10',
    cyan: 'border-cyan-500/30 text-cyan-400 bg-cyan-500/10'
  };

  const style = colorStyles[color] || colorStyles.blue;

  const content = (
    <div className={`glass-panel rounded-xl p-4 relative overflow-hidden transition-all duration-300 h-full ${to ? 'cursor-pointer hover:border-slate-600 hover:scale-[1.02]' : 'hover:border-slate-700'}`}>
      <div className="flex items-center justify-between h-full">
        <div className="flex flex-col justify-center min-h-[56px]">
          <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400 whitespace-nowrap leading-tight">{title}</p>
          <h3 className="text-2xl font-extrabold text-slate-100 font-mono mt-1 leading-tight">{value ?? 0}</h3>
          {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
        </div>
        {Icon && (
          <div className={`p-3 rounded-xl border flex-shrink-0 ${style}`}>
            <Icon className="w-6 h-6" />
          </div>
        )}
      </div>
    </div>
  );

  if (to) {
    return <Link to={to} className="block no-underline">{content}</Link>;
  }
  return content;
};

export default MetricCard;
