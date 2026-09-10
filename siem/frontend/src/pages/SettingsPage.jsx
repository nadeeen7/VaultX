import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Settings, Save, CheckCircle2, Eye } from 'lucide-react';

const SettingsPage = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState({});
  const [savedMessage, setSavedMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [saveError, setSaveError] = useState('');

  const isAdmin = user?.role === 'Admin';

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await api.get('/settings');
      const map = {};
      (res.data.settings || []).forEach((item) => {
        map[item.key] = item.value;
      });
      setSettings(map);
    } catch (err) {
      console.error('Failed to fetch settings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleChange = (key, val) => {
    if (!isAdmin) return; // Prevent changes for non-Admin
    setSettings((prev) => ({ ...prev, [key]: val }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!isAdmin) return;
    setSaveError('');
    try {
      await api.post('/settings', settings);
      setSavedMessage('Settings updated successfully!');
      setTimeout(() => setSavedMessage(''), 4000);
    } catch (err) {
      const msg = err.response?.data?.message || err.response?.data?.error || 'Failed to save settings';
      setSaveError(msg);
      setTimeout(() => setSaveError(''), 5000);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading settings...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">System & Detection Settings</h1>
          <p className="text-xs text-slate-400">Configure SIEM rule thresholds, polling frequencies, and notification webhooks</p>
        </div>
        {!isAdmin && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs">
            <Eye className="w-3.5 h-3.5" />
            <span className="font-semibold">Read-Only Mode</span>
          </div>
        )}
      </div>

      {savedMessage && (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{savedMessage}</span>
        </div>
      )}

      {saveError && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {saveError}
        </div>
      )}

      <form onSubmit={handleSave} className="glass-panel rounded-xl p-6 space-y-6">
        {/* Detection Rule Thresholds */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider border-b border-slate-800 pb-2">
            Rule Engine Threshold Parameters
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-300 font-semibold mb-1">
                Brute Force Threshold (Failed Logins Count)
              </label>
              <input
                type="number"
                value={settings.brute_force_threshold || '5'}
                onChange={(e) => handleChange('brute_force_threshold', e.target.value)}
                readOnly={!isAdmin}
                className={`w-full border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 ${
                  isAdmin ? 'bg-slate-900 focus:border-blue-500 focus:outline-none' : 'bg-slate-800/50 cursor-not-allowed opacity-70'
                }`}
              />
            </div>
            <div>
              <label className="block text-xs text-slate-300 font-semibold mb-1">
                Brute Force Time Window (Minutes)
              </label>
              <input
                type="number"
                value={settings.brute_force_window_mins || '5'}
                onChange={(e) => handleChange('brute_force_window_mins', e.target.value)}
                readOnly={!isAdmin}
                className={`w-full border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 ${
                  isAdmin ? 'bg-slate-900 focus:border-blue-500 focus:outline-none' : 'bg-slate-800/50 cursor-not-allowed opacity-70'
                }`}
              />
            </div>

            <div>
              <label className="block text-xs text-slate-300 font-semibold mb-1">
                Admin Privilege Abuse Threshold
              </label>
              <input
                type="number"
                value={settings.admin_abuse_threshold || '3'}
                onChange={(e) => handleChange('admin_abuse_threshold', e.target.value)}
                readOnly={!isAdmin}
                className={`w-full border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 ${
                  isAdmin ? 'bg-slate-900 focus:border-blue-500 focus:outline-none' : 'bg-slate-800/50 cursor-not-allowed opacity-70'
                }`}
              />
            </div>

            <div>
              <label className="block text-xs text-slate-300 font-semibold mb-1">
                High Request Rate Threshold (req/min)
              </label>
              <input
                type="number"
                value={settings.high_freq_threshold || '20'}
                onChange={(e) => handleChange('high_freq_threshold', e.target.value)}
                readOnly={!isAdmin}
                className={`w-full border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 ${
                  isAdmin ? 'bg-slate-900 focus:border-blue-500 focus:outline-none' : 'bg-slate-800/50 cursor-not-allowed opacity-70'
                }`}
              />
            </div>
          </div>
        </div>

        {/* Notification Webhooks */}
        <div className="space-y-4 pt-4">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider border-b border-slate-800 pb-2">
            Notification Integration Webhooks
          </h3>

          <div className="space-y-3">
            <div>
              <label className="block text-xs text-slate-300 font-semibold mb-1">
                Discord Channel Webhook URL
              </label>
              <input
                type="text"
                placeholder="https://discord.com/api/webhooks/..."
                value={settings.discord_webhook_url || ''}
                onChange={(e) => handleChange('discord_webhook_url', e.target.value)}
                readOnly={!isAdmin}
                className={`w-full border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 font-mono ${
                  isAdmin ? 'bg-slate-900 focus:border-blue-500 focus:outline-none' : 'bg-slate-800/50 cursor-not-allowed opacity-70'
                }`}
              />
            </div>

            <div>
              <label className="block text-xs text-slate-300 font-semibold mb-1">
                Slack Incoming Webhook URL
              </label>
              <input
                type="text"
                placeholder="https://hooks.slack.com/services/..."
                value={settings.slack_webhook_url || ''}
                onChange={(e) => handleChange('slack_webhook_url', e.target.value)}
                readOnly={!isAdmin}
                className={`w-full border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 font-mono ${
                  isAdmin ? 'bg-slate-900 focus:border-blue-500 focus:outline-none' : 'bg-slate-800/50 cursor-not-allowed opacity-70'
                }`}
              />
            </div>
          </div>
        </div>

        {isAdmin && (
          <button
            type="submit"
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-lg transition-colors flex items-center gap-2 shadow-lg shadow-blue-600/20"
          >
            <Save className="w-4 h-4" />
            Save Configurations
          </button>
        )}
      </form>
    </div>
  );
};

export default SettingsPage;
