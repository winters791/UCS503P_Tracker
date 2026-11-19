import { useState } from "react";
import { useAppState } from "../context/AppStateContext";
import {
  CommitmentType,
  RuleType,
  SLOTS_PER_DAY,
  Strictness,
  type Commitment,
} from "../types/domain";
import { slotLabel } from "../utils/time";
import {
  RULE_TYPE_LABEL,
  TIME_BANDS,
  defaultTargetSlot,
  describeRule,
  ruleTypesFor,
} from "../utils/rules";

interface RulesEditorProps {
  commitment: Commitment;
}

export function RulesEditor({ commitment }: RulesEditorProps) {
  const { rules, createRule, deleteRule } = useAppState();
  const available = ruleTypesFor(commitment.type);
  const [ruleType, setRuleType] = useState<RuleType>(available[0] ?? RuleType.TIME_OF_DAY_AFFINITY);
  const [targetSlot, setTargetSlot] = useState(defaultTargetSlot(ruleType));
  const [strictness, setStrictness] = useState<Strictness>(Strictness.SOFT);
  const [busy, setBusy] = useState(false);

  const mine = rules.filter((r) => r.commitment_id === commitment.id);

  if (available.length === 0) {
    return (
      <p className="text-[11px] text-slate-400">Fixed events have an exact slot, so rules do not apply.</p>
    );
  }

  function changeType(next: RuleType) {
    setRuleType(next);
    setTargetSlot(defaultTargetSlot(next));
  }

  async function add() {
    setBusy(true);
    await createRule({ commitment_id: commitment.id, rule_type: ruleType, target_slot: targetSlot, strictness });
    setBusy(false);
  }

  async function remove(id: string) {
    setBusy(true);
    await deleteRule(id);
    setBusy(false);
  }

  const inputClass = "mt-1 w-full rounded-md border border-slate-300 px-2 py-1.5 text-xs";

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
      <div>
        <p className="text-sm font-medium text-slate-700">Scheduling rules</p>
        <p className="text-[11px] text-slate-500">
          Rules save immediately.{" "}
          {commitment.type === CommitmentType.FLEXIBLE_TASK
            ? "Flexible tasks pick them up the next time you re-slot."
            : "Its blocks are re-placed to follow them."}{" "}
          Hard rules are never broken; soft ones are relaxed if they don't fit.
        </p>
      </div>

      {mine.length > 0 && (
        <ul className="flex flex-col gap-1">
          {mine.map((rule) => (
            <li
              key={rule.id}
              className="flex items-center justify-between rounded-md bg-white px-2 py-1 text-xs text-slate-700 border border-slate-200"
            >
              <span>
                {describeRule(rule)}{" "}
                <span className={rule.strictness === Strictness.HARD ? "text-red-600" : "text-slate-400"}>
                  ({rule.strictness.toLowerCase()})
                </span>
              </span>
              <button
                type="button"
                disabled={busy}
                onClick={() => remove(rule.id)}
                className="text-[11px] font-medium text-red-600 hover:text-red-800 disabled:opacity-50"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="grid grid-cols-[1.4fr_1fr_0.8fr] gap-2 items-end">
        <label className="text-[11px] font-medium text-slate-600">
          Rule
          <select value={ruleType} onChange={(e) => changeType(e.target.value as RuleType)} className={inputClass}>
            {available.map((t) => (
              <option key={t} value={t}>
                {RULE_TYPE_LABEL[t]}
              </option>
            ))}
          </select>
        </label>

        <label className="text-[11px] font-medium text-slate-600">
          {ruleType === RuleType.TIME_OF_DAY_AFFINITY && "Band"}
          {ruleType === RuleType.ENERGY_TIERING && "Starts by"}
          {ruleType === RuleType.SEPARATION && "Rest days"}
          {ruleType === RuleType.SEPARATION ? (
            <input
              type="number"
              min={1}
              max={6}
              value={targetSlot}
              onChange={(e) => setTargetSlot(Number(e.target.value))}
              className={inputClass}
            />
          ) : (
            <select value={targetSlot} onChange={(e) => setTargetSlot(Number(e.target.value))} className={inputClass}>
              {ruleType === RuleType.TIME_OF_DAY_AFFINITY
                ? TIME_BANDS.map((band, i) => (
                    <option key={band} value={i}>
                      {band}
                    </option>
                  ))
                : Array.from({ length: SLOTS_PER_DAY }, (_, i) => (
                    <option key={i} value={i}>
                      {slotLabel(i).start}
                    </option>
                  ))}
            </select>
          )}
        </label>

        <label className="text-[11px] font-medium text-slate-600">
          Strictness
          <select
            value={strictness}
            onChange={(e) => setStrictness(e.target.value as Strictness)}
            className={inputClass}
          >
            <option value={Strictness.SOFT}>Soft</option>
            <option value={Strictness.HARD}>Hard</option>
          </select>
        </label>
      </div>

      <button
        type="button"
        disabled={busy}
        onClick={add}
        className="self-start rounded-md bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800 disabled:opacity-50"
      >
        + Add rule
      </button>
    </div>
  );
}
