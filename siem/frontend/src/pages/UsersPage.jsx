import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Users, UserPlus, ShieldOff } from 'lucide-react';

const UsersPage = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Security Analyst');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const isAdmin = user?.role === 'Admin';

  const fetchUsers = async () => {
    try {
      const res = await api.get('/users');
      setUsers(res.data.users);
    } catch (err) {
      console.error('Failed to fetch users:', err);
    }
  };

  useEffect(() => {
    if (isAdmin) fetchUsers();
  }, [isAdmin]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await api.post('/users', { username, email, password, role });
      setSuccess(`User ${username} created successfully.`);
      setUsername('');
      setEmail('');
      setPassword('');
      fetchUsers();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create user');
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await api.patch(`/users/${userId}/role`, { role: newRole });
      fetchUsers();
    } catch (err) {
      console.error('Failed to update user role:', err);
    }
  };

  // Safety net: non-Admin who navigates directly here
  if (!isAdmin) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto">
            <ShieldOff className="w-8 h-8 text-red-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100">Access Denied</h2>
            <p className="text-sm text-slate-400 mt-1">
              User Management requires Admin privileges.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">User Management & RBAC</h1>
        <p className="text-xs text-slate-400">Manage SOC user accounts and role permissions (Admin, Security Analyst, Viewer)</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Users List Table */}
        <div className="glass-panel rounded-xl p-5 lg:col-span-2 overflow-x-auto">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider mb-4">Active SOC Analysts & Users</h3>
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-3">ID</th>
                <th className="p-3">Username</th>
                <th className="p-3">Email</th>
                <th className="p-3">Current Role</th>
                <th className="p-3">Update Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-3 font-mono text-slate-400">#{u.id}</td>
                  <td className="p-3 font-semibold text-slate-200">{u.username}</td>
                  <td className="p-3 text-slate-300">{u.email}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-blue-500/20 text-blue-300 font-mono">
                      {u.role}
                    </span>
                  </td>
                  <td className="p-3">
                    <select
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none"
                    >
                      <option value="Admin">Admin</option>
                      <option value="Security Analyst">Security Analyst</option>
                      <option value="Viewer">Viewer</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Create User Form */}
        <div className="glass-panel rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <UserPlus className="w-4 h-4 text-blue-400" /> Provision New User
          </h3>

          {error && <div className="p-2 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">{error}</div>}
          {success && <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs">{success}</div>}

          <form onSubmit={handleCreateUser} className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-300 mb-1">Username</label>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-100"
              />
            </div>
            <div>
              <label className="block text-slate-300 mb-1">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-100"
              />
            </div>
            <div>
              <label className="block text-slate-300 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-100"
              />
            </div>
            <div>
              <label className="block text-slate-300 mb-1">Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-100"
              >
                <option value="Security Analyst">Security Analyst</option>
                <option value="Admin">Admin</option>
                <option value="Viewer">Viewer</option>
              </select>
            </div>

            <button type="submit" className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg">
              Create User Account
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UsersPage;
