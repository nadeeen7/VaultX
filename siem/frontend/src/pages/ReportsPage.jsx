import React, { useState } from 'react';
import api from '../services/api';
import { FileText, Download, FileSpreadsheet, Code, ShieldCheck, Loader2 } from 'lucide-react';

const ReportsPage = () => {
  const [downloading, setDownloading] = useState(null);

  const handleDownload = async (endpoint, filename, type) => {
    setDownloading(type);
    try {
      const res = await api.get(endpoint, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
      alert('Download failed. Please try again.');
    } finally {
      setDownloading(null);
    }
  };

  const downloadPdf = () => handleDownload('/reports/pdf', 'mini_siem_executive_report.pdf', 'pdf');
  const downloadCsv = () => handleDownload('/reports/csv', 'mini_siem_events_export.csv', 'csv');
  const downloadJson = () => handleDownload('/reports/json', 'mini_siem_security_dump.json', 'json');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Security Reports & Compliance</h1>
        <p className="text-xs text-slate-400">Generate executive PDF summaries, CSV logs, and JSON telemetry exports</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* PDF Executive Report */}
        <div className="glass-panel rounded-xl p-6 flex flex-col justify-between hover:border-slate-700 transition-all">
          <div>
            <div className="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center justify-center mb-4">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-100 text-lg mb-2">Executive PDF Security Report</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Comprehensive report containing executive summaries, alert breakdowns, top attacker IPs, MITRE ATT&CK techniques, and defensive SOC recommendations.
            </p>
          </div>
          <button
            onClick={downloadPdf}
            disabled={downloading === 'pdf'}
            className="w-full py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs rounded-lg transition-colors flex items-center justify-center gap-2 shadow-lg shadow-rose-600/20 disabled:opacity-50"
          >
            {downloading === 'pdf' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            {downloading === 'pdf' ? 'Generating...' : 'Download PDF Report'}
          </button>
        </div>

        {/* CSV Log Export */}
        <div className="glass-panel rounded-xl p-6 flex flex-col justify-between hover:border-slate-700 transition-all">
          <div>
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mb-4">
              <FileSpreadsheet className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-100 text-lg mb-2">CSV Security Events Export</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Export raw security events, alert logs, risk scores, and IP metadata formatted as a CSV spreadsheet for external audit analysis.
            </p>
          </div>
          <button
            onClick={downloadCsv}
            disabled={downloading === 'csv'}
            className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-lg transition-colors flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/20 disabled:opacity-50"
          >
            {downloading === 'csv' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            {downloading === 'csv' ? 'Exporting...' : 'Export CSV File'}
          </button>
        </div>

        {/* JSON Dump Export */}
        <div className="glass-panel rounded-xl p-6 flex flex-col justify-between hover:border-slate-700 transition-all">
          <div>
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 flex items-center justify-center mb-4">
              <Code className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-100 text-lg mb-2">JSON Full Posture Dump</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Complete SIEM state dump in structured JSON format including all events, alerts, incidents, and threat intelligence metadata.
            </p>
          </div>
          <button
            onClick={downloadJson}
            disabled={downloading === 'json'}
            className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs rounded-lg transition-colors flex items-center justify-center gap-2 shadow-lg shadow-cyan-600/20 disabled:opacity-50"
          >
            {downloading === 'json' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            {downloading === 'json' ? 'Exporting...' : 'Download JSON Dump'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
