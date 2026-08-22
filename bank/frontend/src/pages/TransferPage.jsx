import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createTransfer } from "../services/api.js";
import Alert from "../components/Alert.jsx";
import {
  ArrowUpRight,
  Check,
  ArrowLeft,
  ArrowRight,
  Shield,
} from "lucide-react";

export default function TransferPage() {
  const [form, setForm] = useState({
    recipient_account: "",
    recipient_name: "",
    amount: "",
    description: "",
  });
  const [step, setStep] = useState(1); // 1 = form, 2 = confirm, 3 = success
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError("");
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.recipient_account || !form.amount) {
      setError("Recipient account and amount are required");
      return;
    }
    if (parseFloat(form.amount) <= 0) {
      setError("Amount must be positive");
      return;
    }
    if (parseFloat(form.amount) > 100000) {
      setError("Maximum transfer amount is $100,000");
      return;
    }
    setStep(2);
  };

  const handleConfirm = async () => {
    setLoading(true);
    setError("");
    try {
      await createTransfer({
        recipient_account: form.recipient_account,
        recipient_name: form.recipient_name || "Unknown",
        amount: parseFloat(form.amount),
        description: form.description || "Transfer",
      });
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.error || "Transfer failed");
      setStep(1);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setStep(1);
    setForm({ recipient_account: "", recipient_name: "", amount: "", description: "" });
    setError("");
  };

  // Success state
  if (step === 3) {
    return (
      <div className="p-4 sm:p-6 lg:p-8 max-w-2xl mx-auto">
        <div className="card p-8 sm:p-12 text-center animate-slide-up">
          <div className="w-16 h-16 bg-emerald-50 dark:bg-emerald-900/20 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <Check className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
          </div>
          <h2 className="text-2xl font-bold text-navy-900 dark:text-white mb-2">Transfer Successful</h2>
          <p className="text-gray-500 dark:text-slate-400 mb-2">
            Your transfer of <span className="font-semibold text-navy-900 dark:text-white">${parseFloat(form.amount).toFixed(2)}</span> has been processed.
          </p>
          <p className="text-sm text-gray-400 dark:text-slate-500 mb-8">
            To account {form.recipient_account}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button onClick={resetForm} className="btn-primary">
              <ArrowUpRight className="w-4 h-4" />
              New Transfer
            </button>
            <button onClick={() => navigate("/dashboard")} className="btn-secondary">
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Send Money</h1>
        <p className="text-gray-500 dark:text-slate-400 mt-1">Transfer funds securely to another account</p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-3 mb-6">
        {[1, 2].map((s) => (
          <div key={s} className="flex items-center gap-3 flex-1">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
              step >= s ? "bg-navy-800 text-white" : "bg-gray-100 dark:bg-slate-700 text-gray-400 dark:text-slate-500"
            }`}>
              {step > s ? <Check className="w-4 h-4" /> : s}
            </div>
            <span className={`text-sm font-medium ${step >= s ? "text-navy-900 dark:text-white" : "text-gray-400 dark:text-slate-500"}`}>
              {s === 1 ? "Details" : "Confirm"}
            </span>
            {s < 2 && <div className={`flex-1 h-0.5 rounded ${step > s ? "bg-navy-800" : "bg-gray-200 dark:bg-slate-700"}`} />}
          </div>
        ))}
      </div>

      {/* Error */}
      {error && <Alert type="error" message={error} onClose={() => setError("")} />}

      {step === 1 ? (
        /* Transfer Form */
        <form onSubmit={handleSubmit} className="card p-6 space-y-5 animate-fade-in">
          <div>
            <label className="label">Recipient Account Number *</label>
            <input
              type="text"
              name="recipient_account"
              value={form.recipient_account}
              onChange={handleChange}
              required
              placeholder="e.g. SB1234567890"
              className="input-field font-mono"
            />
          </div>

          <div>
            <label className="label">Recipient Name</label>
            <input
              type="text"
              name="recipient_name"
              value={form.recipient_name}
              onChange={handleChange}
              placeholder="John Doe"
              className="input-field"
            />
          </div>

          <div>
            <label className="label">Amount (USD) *</label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-slate-500 font-medium">$</span>
              <input
                type="number"
                name="amount"
                value={form.amount}
                onChange={handleChange}
                required
                min="0.01"
                step="0.01"
                placeholder="0.00"
                className="input-field !pl-8 font-mono text-lg"
              />
            </div>
          </div>

          <div>
            <label className="label">Description</label>
            <input
              type="text"
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Payment for..."
              className="input-field"
            />
          </div>

          <button type="submit" className="btn-primary w-full !py-3">
            Review Transfer
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      ) : (
        /* Confirmation */
        <div className="card p-6 animate-fade-in">
          <h3 className="text-base font-semibold text-navy-900 dark:text-white mb-5">Confirm Transfer</h3>

          <div className="bg-slate-50 dark:bg-slate-900 rounded-xl p-5 space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500 dark:text-slate-400">To Account</span>
              <span className="font-mono text-sm font-semibold text-navy-900 dark:text-white">{form.recipient_account}</span>
            </div>
            {form.recipient_name && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500 dark:text-slate-400">Recipient</span>
                <span className="text-sm font-medium text-navy-900 dark:text-white">{form.recipient_name}</span>
              </div>
            )}
            <div className="border-t border-gray-200 dark:border-slate-700 pt-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500 dark:text-slate-400">Amount</span>
                <span className="text-2xl font-bold text-navy-900 dark:text-white">${parseFloat(form.amount).toFixed(2)}</span>
              </div>
            </div>
            {form.description && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500 dark:text-slate-400">Description</span>
                <span className="text-sm text-navy-900 dark:text-white">{form.description}</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 mt-4 mb-6 text-gray-400 dark:text-slate-500">
            <Shield className="w-3.5 h-3.5" />
            <span className="text-xs">This transfer is encrypted and secure</span>
          </div>

          <div className="flex gap-3">
            <button onClick={() => setStep(1)} className="btn-secondary flex-1">
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <button onClick={handleConfirm} disabled={loading} className="btn-primary flex-1">
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  Confirm Transfer
                  <Check className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
