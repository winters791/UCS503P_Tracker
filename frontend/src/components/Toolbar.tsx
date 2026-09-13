import { useAppState } from "../context/AppStateContext";

export function Toolbar() {
  const { solveSchedule, mode, commitments } = useAppState();
  const solving = mode === "solving";

  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-5 py-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Ops — Weekly Canvas</h1>
        <p className="text-xs text-slate-500">
          {commitments.length} active commitment{commitments.length === 1 ? "" : "s"}
        </p>
      </div>
      <button
        onClick={solveSchedule}
        disabled={solving}
        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
      >
        {solving && (
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
        )}
        {solving ? "Generating…" : "Generate Weekly Schedule"}
      </button>
    </div>
  );
}
