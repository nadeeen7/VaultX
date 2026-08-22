import { Link } from "react-router-dom";
import {
  Shield,
  Activity,
  CreditCard,
  Lock,
  Eye,
  Zap,
  ArrowRight,
  ChevronRight,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-900">
      {/* Hero */}
      <section className="relative bg-navy-900 overflow-hidden">
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: '40px 40px',
          }}
        />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-32">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/10 rounded-full px-4 py-1.5 mb-8">
              <Shield className="w-3.5 h-3.5 text-accent-400" />
              <span className="text-xs font-medium text-white/80">Cybersecurity Training Platform</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight leading-tight mb-6">
              Secure Digital
              <br />
              <span className="text-accent-400">Banking Platform</span>
            </h1>
            <p className="text-lg text-gray-400 mb-10 max-w-xl mx-auto leading-relaxed">
              A realistic banking application integrated with SIEM for real-time security monitoring, detection, and incident response.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                to="/login"
                className="btn-primary !bg-white !text-navy-900 hover:!bg-gray-100 !px-8 !py-3.5 text-base w-full sm:w-auto"
              >
                Sign In
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/register"
                className="inline-flex items-center justify-center gap-2 px-8 py-3.5 text-base w-full sm:w-auto rounded-lg font-semibold transition-all duration-200 bg-white/10 backdrop-blur-sm border border-white/30 text-white hover:bg-white/20 hover:border-white/50"
              >
                Create Account
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-navy-900 dark:text-white mb-3">Platform Capabilities</h2>
          <p className="text-gray-500 dark:text-slate-400 max-w-lg mx-auto">
            Built for cybersecurity training with enterprise-grade architecture
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              icon: Lock,
              title: "Authentication & Security",
              desc: "JWT authentication, bcrypt password hashing, account lockout, and role-based access control.",
            },
            {
              icon: Activity,
              title: "Real-time SIEM Events",
              desc: "Every user action generates structured security events, pushed to SentinelSIEM for monitoring and detection.",
            },
            {
              icon: CreditCard,
              title: "Banking Operations",
              desc: "Transfers, transaction history, account management — a fully functional banking interface.",
            },
            {
              icon: Eye,
              title: "Threat Detection",
              desc: "Automated detection of brute force attacks, account compromise, privilege abuse, and anomalous behavior.",
            },
            {
              icon: Shield,
              title: "MITRE ATT&CK Mapping",
              desc: "Security events mapped to MITRE ATT&CK techniques for professional threat analysis.",
            },
            {
              icon: Zap,
              title: "ML Anomaly Detection",
              desc: "Isolation Forest algorithm identifies unusual patterns and generates risk scores with transparent factors.",
            },
          ].map((f) => (
            <div key={f.title} className="card-hover p-6 group">
              <div className="w-10 h-10 bg-navy-50 dark:bg-navy-900/30 rounded-lg flex items-center justify-center mb-4 group-hover:bg-navy-100 dark:group-hover:bg-navy-900/50 transition-colors">
                <f.icon className="w-5 h-5 text-navy-700 dark:text-navy-300" />
              </div>
              <h3 className="text-base font-semibold text-navy-900 dark:text-white mb-2">{f.title}</h3>
              <p className="text-sm text-gray-500 dark:text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Security Events */}
      <section className="bg-white dark:bg-slate-800/50 border-y border-gray-100 dark:border-slate-700/50 py-20 sm:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-navy-900 dark:text-white mb-3">Security Events Generated</h2>
            <p className="text-gray-500 dark:text-slate-400">Structured logging for every user interaction</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-4xl mx-auto">
            {[
              "LOGIN_SUCCESS", "LOGIN_FAILED", "LOGOUT", "ACCOUNT_LOCKED",
              "TRANSFER_CREATED", "TRANSFER_FAILED", "PASSWORD_CHANGE",
              "UNAUTHORIZED_ACCESS", "SUSPICIOUS_REQUEST", "ADMIN_LOGIN",
              "ACCOUNT_CREATED", "ADMIN_LOGIN_FAILED",
            ].map((event) => (
              <div
                key={event}
                className="flex items-center gap-2 px-4 py-2.5 bg-slate-50 dark:bg-slate-900 rounded-lg border border-gray-100 dark:border-slate-700 font-mono text-xs text-navy-700 dark:text-navy-300"
              >
                <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                  event.includes("SUCCESS") || event === "LOGOUT" || event === "ACCOUNT_CREATED" || event === "TRANSFER_CREATED" || event === "PASSWORD_CHANGE" || event === "ADMIN_LOGIN"
                    ? "bg-emerald-500"
                    : event.includes("FAILED") || event.includes("LOCKED") || event.includes("UNAUTHORIZED") || event.includes("SUSPICIOUS")
                    ? "bg-red-500"
                    : "bg-gray-400 dark:bg-slate-500"
                }`} />
                {event}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-24">
        <div className="bg-navy-900 rounded-2xl p-8 sm:p-12 text-center relative overflow-hidden">
          <div className="absolute inset-0 opacity-5"
            style={{
              backgroundImage: `radial-gradient(circle at 2px 2px, white 1px, transparent 0)`,
              backgroundSize: '32px 32px',
            }}
          />
          <div className="relative">
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">Ready to get started?</h2>
            <p className="text-gray-400 mb-8 max-w-md mx-auto">
              Create an account and explore the full banking and security monitoring experience.
            </p>
            <Link
              to="/register"
              className="inline-flex items-center justify-center gap-2 px-8 py-3 bg-white hover:bg-gray-100 text-navy-900 font-medium rounded-lg transition-all duration-200 text-sm"
            >
              Create Free Account
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-slate-700/50 bg-white dark:bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-navy-800 rounded-md flex items-center justify-center">
                <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <span className="font-semibold text-navy-900 dark:text-white text-sm">VaultX</span>
            </div>
            <p className="text-xs text-gray-400 dark:text-slate-500">
              Cybersecurity Training Platform — All data is simulated. No real banking operations.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
