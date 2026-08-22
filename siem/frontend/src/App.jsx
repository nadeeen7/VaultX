import React from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import EventsPage from './pages/EventsPage';
import AlertsPage from './pages/AlertsPage';
import AlertDetailPage from './pages/AlertDetailPage';
import IncidentsPage from './pages/IncidentsPage';
import IncidentDetailPage from './pages/IncidentDetailPage';
import TimelinePage from './pages/TimelinePage';
import MitrePage from './pages/MitrePage';
import IPIntelligencePage from './pages/IPIntelligencePage';
import AnalyticsPage from './pages/AnalyticsPage';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';
import UsersPage from './pages/UsersPage';

const ProtectedLayout = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 font-mono text-xs">Authenticating SIEM session...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        <main className="p-6 flex-1 overflow-y-auto custom-scrollbar">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<ProtectedLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/alerts/:id" element={<AlertDetailPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/incidents/:id" element={<IncidentDetailPage />} />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/mitre" element={<MitrePage />} />
          <Route path="/ip-intelligence" element={<IPIntelligencePage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/users" element={<UsersPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
