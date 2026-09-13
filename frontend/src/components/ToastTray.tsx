import { useToast } from "../context/ToastContext";

const KIND_STYLES: Record<string, string> = {
  error: "bg-red-600 text-white",
  success: "bg-emerald-600 text-white",
  info: "bg-slate-800 text-white",
};

export function ToastTray() {
  const { toasts, dismissToast } = useToast();

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`rounded-lg px-4 py-3 shadow-lg text-sm flex items-start justify-between gap-3 ${KIND_STYLES[toast.kind]}`}
        >
          <span className="leading-snug">{toast.message}</span>
          <button
            onClick={() => dismissToast(toast.id)}
            className="opacity-70 hover:opacity-100 shrink-0"
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
