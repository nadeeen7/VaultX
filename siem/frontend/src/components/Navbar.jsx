import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, User, Radio } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-10">
      {/* Realtime Live Socket Indicator */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
          <Radio className="w-3.5 h-3.5 animate-pulse" />
          <span>Real-Time Monitor Active</span>
        </div>
      </div>

      {/* User Actions */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700">
          <User className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-medium text-slate-200">{user?.username}</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono">
            {user?.role}
          </span>
        </div>

        <button
          onClick={logout}
          className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
          title="Sign out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};

export default Navbar;
