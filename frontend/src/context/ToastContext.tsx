import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

interface Toast {
  id: number;
  message: string;
  kind: "error" | "success" | "info";
}

interface ToastContextValue {
  toasts: Toast[];
  pushToast: (message: string, kind?: Toast["kind"]) => void;
  dismissToast: (id: number) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let nextId = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const pushToast = useCallback(
    (message: string, kind: Toast["kind"] = "info") => {
      const id = nextId++;
      setToasts((prev) => [...prev, { id, message, kind }]);
      setTimeout(() => dismissToast(id), 5000);
    },
    [dismissToast],
  );

  return (
    <ToastContext.Provider value={{ toasts, pushToast, dismissToast }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
