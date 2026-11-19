import { useAppState } from "../context/AppStateContext";

export type View = "planner" | "review";

interface ToolbarProps {
  view: View;
  onChangeView: (view: View) => void;
}

const TABS: { id: View; label: string }[] = [
  { id: "planner", label: "Planner" },
  { id: "review", label: "Review" },
];

export function Toolbar({ view, onChangeView }: ToolbarProps) {
  const { commitments } = useAppState();

  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white px-5 py-4">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">
          Ops — {view === "planner" ? "Weekly Canvas" : "Weekly Review"}
        </h1>
        <p className="text-xs text-slate-500">
          {commitments.length} active commitment{commitments.length === 1 ? "" : "s"}
        </p>
      </div>

      <nav className="flex rounded-lg bg-slate-100 p-1" aria-label="View">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChangeView(tab.id)}
            aria-current={view === tab.id ? "page" : undefined}
            className={`rounded-md px-4 py-1.5 text-sm font-medium ${
              view === tab.id ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-800"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <p className="text-xs text-slate-400 max-w-xs text-right">
        {view === "planner"
          ? "Drag a commitment from the sidebar onto any open block to schedule it."
          : "Built from your execution logs. Mark blocks done or missed on the planner to fill it in."}
      </p>
    </div>
  );
}
