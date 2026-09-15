import { useAppState } from "../context/AppStateContext";

export function Toolbar() {
  const { commitments } = useAppState();

  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-5 py-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Ops — Weekly Canvas</h1>
        <p className="text-xs text-slate-500">
          {commitments.length} active commitment{commitments.length === 1 ? "" : "s"}
        </p>
      </div>
      <p className="text-xs text-slate-400 max-w-xs text-right">
        Drag a commitment from the sidebar onto any open block to schedule it.
      </p>
    </div>
  );
}
