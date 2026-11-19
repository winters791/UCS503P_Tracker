import { DAYS_OF_WEEK, type RetrospectiveReport } from "../types/domain";
import { TYPE_STYLES } from "../utils/blockStyles";
import { formatShort } from "../utils/dates";

interface RetrospectivePanelProps {
  report: RetrospectiveReport | null;
  isCurrentWeek: boolean;
  onPrevWeek: () => void;
  onNextWeek: () => void;
}

export function RetrospectivePanel({ report, isCurrentWeek, onPrevWeek, onNextWeek }: RetrospectivePanelProps) {
  const t = report?.totals;
  const rate = t && t.due > 0 ? `${Math.round((100 * t.completed) / t.due)}%` : "—";

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 flex flex-col gap-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">Weekly retrospective</h2>
          <p className="text-[11px] text-slate-500">Planned blocks against what you logged.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onPrevWeek}
            className="rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50"
            aria-label="Previous week"
          >
            ‹
          </button>
          <span className="text-xs font-medium text-slate-700 tabular-nums min-w-32 text-center">
            {report ? `${formatShort(report.week_start)} – ${formatShort(report.week_end)}` : "…"}
            {isCurrentWeek && <span className="block text-[10px] font-normal text-slate-400">this week</span>}
          </span>
          <button
            onClick={onNextWeek}
            disabled={isCurrentWeek}
            className="rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-30"
            aria-label="Next week"
          >
            ›
          </button>
        </div>
      </div>

      {!report && <p className="text-xs text-slate-400">Loading…</p>}

      {report && t && (
        <>
          <div className="grid grid-cols-5 gap-3">
            {[
              ["Completion", rate, "text-slate-900"],
              ["Done", t.completed, "text-emerald-700"],
              ["Missed", t.missed, "text-red-600"],
              ["Not logged", t.not_logged, "text-amber-600"],
              ["Upcoming", t.upcoming, "text-slate-500"],
            ].map(([label, value, color]) => (
              <div key={label} className="rounded-lg bg-slate-50 px-3 py-2">
                <p className={`text-xl font-semibold tabular-nums ${color}`}>{value}</p>
                <p className="text-[11px] text-slate-500">{label}</p>
              </div>
            ))}
          </div>

          <ul className="flex flex-col gap-1.5 rounded-lg border border-slate-200 px-4 py-3">
            {report.highlights.map((h) => (
              <li key={h} className="text-sm text-slate-700 flex gap-2">
                <span className="text-slate-400">•</span>
                {h}
              </li>
            ))}
          </ul>

          <div className="grid grid-cols-7 gap-2">
            {report.by_day.map((d, i) => {
              const pct = d.due ? Math.round((100 * d.completed) / d.due) : 0;
              return (
                <div key={DAYS_OF_WEEK[i]} className="flex flex-col items-center gap-1">
                  <div className="relative h-16 w-full max-w-10 rounded bg-slate-100 overflow-hidden">
                    <div className="absolute bottom-0 w-full bg-emerald-500" style={{ height: `${pct}%` }} />
                  </div>
                  <p className="text-[11px] font-medium text-slate-700">{DAYS_OF_WEEK[i].slice(0, 3)}</p>
                  <p className="text-[10px] tabular-nums text-slate-500">
                    {d.due ? `${d.completed}/${d.due}` : d.upcoming ? `${d.upcoming} ahead` : "—"}
                  </p>
                </div>
              );
            })}
          </div>

          {report.by_commitment.length > 0 && (
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-[11px] text-slate-500 border-b border-slate-200">
                  <th className="py-1.5 font-medium">Commitment</th>
                  <th className="py-1.5 font-medium text-right">Planned</th>
                  <th className="py-1.5 font-medium text-right">Done</th>
                  <th className="py-1.5 font-medium text-right">Missed</th>
                  <th className="py-1.5 font-medium text-right">Not logged</th>
                  <th className="py-1.5 font-medium text-right">Upcoming</th>
                </tr>
              </thead>
              <tbody>
                {report.by_commitment.map((c) => (
                  <tr key={c.commitment_id} className="border-b border-slate-100 last:border-0">
                    <td className="py-1.5 text-slate-800">
                      <span className={`mr-2 inline-block h-2 w-2 rounded-full ${TYPE_STYLES[c.type].dot}`} />
                      {c.title}
                    </td>
                    <td className="py-1.5 text-right tabular-nums text-slate-600">{c.tally.planned}</td>
                    <td className="py-1.5 text-right tabular-nums text-emerald-700">{c.tally.completed || ""}</td>
                    <td className="py-1.5 text-right tabular-nums text-red-600">{c.tally.missed || ""}</td>
                    <td className="py-1.5 text-right tabular-nums text-amber-600">{c.tally.not_logged || ""}</td>
                    <td className="py-1.5 text-right tabular-nums text-slate-400">{c.tally.upcoming || ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </section>
  );
}
