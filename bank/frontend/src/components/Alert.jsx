import { AlertCircle, CheckCircle, AlertTriangle, Info, X } from "lucide-react";

const config = {
  error: {
    styles: "bg-red-50 text-red-800 border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-800/40",
    icon: AlertCircle,
  },
  success: {
    styles: "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-300 dark:border-emerald-800/40",
    icon: CheckCircle,
  },
  warning: {
    styles: "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-900/20 dark:text-amber-300 dark:border-amber-800/40",
    icon: AlertTriangle,
  },
  info: {
    styles: "bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-800/40",
    icon: Info,
  },
};

export default function Alert({ type = "error", message, onClose }) {
  if (!message) return null;

  const { styles, icon: Icon } = config[type] || config.error;

  return (
    <div className={`border rounded-lg p-3.5 ${styles} flex items-start gap-3 animate-fade-in`}>
      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
      <span className="text-sm flex-1">{message}</span>
      {onClose && (
        <button
          onClick={onClose}
          className="p-0.5 rounded hover:bg-black/5 dark:hover:bg-white/10 transition-colors flex-shrink-0"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
