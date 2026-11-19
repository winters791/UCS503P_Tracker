import type { ConsistencyReport } from "../types/domain";
import { formatShort } from "../utils/dates";

interface ConsistencyPanelProps {
  report: ConsistencyReport | null;
}

export function ConsistencyPanel({ report }: ConsistencyPanelProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-slate-900">Weekly consistency</h2>
        <p className="text-[11px] text-slate-500">
          Sessions done against each weekly target. A streak only breaks when a whole week closes short —
          a missed day mid-week costs nothing.
        </p>
      </div>

      {!report && <p className="text-xs text-slate-400">Loading…</p>}
      {report && report.quotas.length === 0 && (
        <p className="text-xs text-slate-400">
          No recurring quotas yet. Add one (e.g. Gym, 4 per week) to track consistency here.
        </p>
      )}

      <ul className="flex flex-col divide-y divide-slate-100">
        {report?.quotas.map((q) => {
          const pct = Math.min(100, Math.round((100 * q.completed_this_week) / q.target));
          const met = q.completed_this_week >= q.target;
          return (
            <li key={q.commitment_id} className="py-3 flex flex-col gap-2">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-800 truncate">{q.title}</p>
                  <p className="text-xs tabular-nums text-slate-600">
                    <span className={met ? "font-semibold text-emerald-700" : "font-semibold text-slate-900"}>
                      {q.completed_this_week}
                    </span>{" "}
                    / {q.target} this week
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-lg font-semibold tabular-nums leading-none text-slate-900">{q.streak}</p>
                  <p className="text-[10px] text-slate-500">week streak</p>
                </div>
              </div>

              <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className={`h-full rounded-full ${met ? "bg-emerald-500" : "bg-slate-400"}`}
                  style={{ width: `${pct}%` }}
                />
              </div>

              <div className="flex items-center gap-1" aria-label={`Last ${q.history.length} weeks`}>
                {q.history.map((w, i) => {
                  const current = i === q.history.length - 1;
                  return (
                    <span
                      key={w.week_start}
                      title={`Week of ${formatShort(w.week_start)}: ${w.completed}/${q.target}${current ? " (in progress)" : ""}`}
                      className={`h-3.5 w-3.5 rounded-sm ${w.met ? "bg-emerald-500" : current ? "bg-white" : "bg-slate-200"} ${current ? "ring-1 ring-slate-400" : ""}`}
                    />
                  );
                })}
                <span className="ml-2 text-[10px] text-slate-400">last {q.history.length} weeks</span>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
