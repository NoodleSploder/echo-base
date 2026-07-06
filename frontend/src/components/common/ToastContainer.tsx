import { useToast, type ToastVariant } from "../../context/ToastContext";

const VARIANT_CLASSES: Record<ToastVariant, string> = {
  info: "border-accent-500/40 bg-base-900 text-slate-200",
  warning: "border-amber-500/50 bg-base-900 text-amber-100",
  danger: "border-red-500/50 bg-base-900 text-red-100",
};

const VARIANT_DOT: Record<ToastVariant, string> = {
  info: "bg-accent-400",
  warning: "bg-amber-400",
  danger: "bg-red-400",
};

export function ToastContainer() {
  const { toasts, dismissToast } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`pointer-events-auto flex items-start gap-2 rounded-md border px-3 py-2 shadow-lg shadow-black/30 ${VARIANT_CLASSES[toast.variant]}`}
        >
          <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${VARIANT_DOT[toast.variant]}`} />
          <div className="min-w-0 flex-1">
            <div className="text-sm font-medium">{toast.title}</div>
            {toast.message && <div className="mt-0.5 text-xs opacity-80">{toast.message}</div>}
          </div>
          <button
            type="button"
            onClick={() => dismissToast(toast.id)}
            className="shrink-0 text-xs text-slate-500 hover:text-slate-300"
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
