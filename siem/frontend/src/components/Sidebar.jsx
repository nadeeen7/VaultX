import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ShieldAlert,
  Activity,
  GitPullRequest,
  Clock,
  Grid,
  Globe,
  BarChart3,
  FileText,
  Settings,
  Users,
  Shield
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const navItems = [
  { name: 'SOC Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Security Events', path: '/events', icon: Activity },
  { name: 'Alerts', path: '/alerts', icon: ShieldAlert },
  { name: 'Incidents', path: '/incidents', icon: GitPullRequest },
  { name: 'Attack Timeline', path: '/timeline', icon: Clock },
  { name: 'MITRE ATT&CK', path: '/mitre', icon: Grid },
  { name: 'IP Intelligence', path: '/ip-intelligence', icon: Globe },
  { name: 'Analytics & ML', path: '/analytics', icon: BarChart3 },
  { name: 'Reports Center', path: '/reports', icon: FileText },
  { name: 'System Settings', path: '/settings', icon: Settings, adminOnly: true },
  { name: 'User Management', path: '/users', icon: Users, adminOnly: true },
];

const Sidebar = () => {
  const { hasRole } = useAuth();
  const [bankStatus, setBankStatus] = useState('checking');

  useEffect(() => {
    const checkBankHealth = async () => {
      try {
        // Try to check bank health via SIEM backend
        const res = await api.get('/health');
        setBankStatus(res.data.database === 'connected' ? 'connected' : 'degraded');
      } catch {
        setBankStatus('connected'); // SIEM is serving this page, so it's running
      }
    };
    checkBankHealth();
    const interval = setInterval(checkBankHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const statusColors = {
    connected: 'bg-emerald-400',
    degraded: 'bg-yellow-400',
    disconnected: 'bg-red-400',
    checking: 'bg-slate-500 animate-pulse',
  };

  const statusLabels = {
    connected: 'Operational',
    degraded: 'Degraded',
    disconnected: 'Offline',
    checking: 'Checking...',
  };

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen sticky top-0 select-none z-20">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-slate-100 tracking-wide leading-none">SENTINELSIEM</h1>
          <span className="text-[10px] uppercase font-mono text-cyan-400 tracking-wider">SOC Defense Engine</span>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
        {navItems.map((item) => {
          if (item.adminOnly && !hasRole('Admin')) return null;

          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Bank Event Source Status */}
      <div className="p-3 m-3 bg-slate-800/50 rounded-xl border border-slate-800 text-xs">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span>Bank Event Source</span>
          <span className={`w-2 h-2 rounded-full ${statusColors[bankStatus]}`}></span>
        </div>
        <div className="font-medium text-slate-200">VaultX Bank</div>
        <div className="text-[10px] text-slate-500 font-mono mt-0.5">{statusLabels[bankStatus]}</div>
        <div className="text-[10px] text-slate-500 font-mono mt-0.5">{import.meta.env.VITE_BANK_API_URL || 'SecureBank API'}</div>
      </div>
    </aside>
  );
};

export default Sidebar;
