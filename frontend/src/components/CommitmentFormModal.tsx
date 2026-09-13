import { useEffect, useState } from "react";
import { useAppState } from "../context/AppStateContext";
import {
  CommitmentType,
  DayOfWeek,
  DAYS_OF_WEEK,
  SLOTS_PER_DAY,
  COMMITMENT_TYPE_LABEL,
  type Commitment,
  type CommitmentCreate,
} from "../types/domain";

interface CommitmentFormModalProps {
  editing: Commitment | null;
  onClose: () => void;
}

const EMPTY_FORM: CommitmentCreate = {
  title: "",
  type: CommitmentType.FLEXIBLE_TASK,
  target_per_week: null,
  duration_blocks: 1,
  priority: 100,
  day: null,
  slot_index: null,
  deadline_day: null,
  deadline_slot: null,
};

export function CommitmentFormModal({ editing, onClose }: CommitmentFormModalProps) {
  const { createCommitment, updateCommitment } = useAppState();
  const [form, setForm] = useState<CommitmentCreate>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (editing) {
      const { id: _id, ...rest } = editing;
      setForm(rest);
    } else {
      setForm(EMPTY_FORM);
    }
  }, [editing]);

  function update<K extends keyof CommitmentCreate>(key: K, value: CommitmentCreate[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    const ok = editing
      ? await updateCommitment(editing.id, form)
      : await createCommitment(form);
    setSaving(false);
    if (ok) onClose();
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">
          {editing ? "Edit Commitment" : "New Commitment"}
        </h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <label className="text-sm font-medium text-slate-700">
            Title
            <input
              required
              value={form.title}
              onChange={(e) => update("title", e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </label>

          <label className="text-sm font-medium text-slate-700">
            Type
            <select
              value={form.type}
              onChange={(e) => update("type", e.target.value as CommitmentType)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              {Object.values(CommitmentType).map((t) => (
                <option key={t} value={t}>
                  {COMMITMENT_TYPE_LABEL[t]}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm font-medium text-slate-700">
            Priority (lower = higher priority)
            <input
              type="number"
              value={form.priority}
              onChange={(e) => update("priority", Number(e.target.value))}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </label>

          <label className="text-sm font-medium text-slate-700">
            Duration (50-min blocks)
            <input
              type="number"
              min={1}
              value={form.duration_blocks}
              onChange={(e) => update("duration_blocks", Number(e.target.value))}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </label>

          {form.type === CommitmentType.FIXED_EVENT && (
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm font-medium text-slate-700">
                Day
                <select
                  value={form.day ?? ""}
                  onChange={(e) => update("day", (e.target.value || null) as DayOfWeek | null)}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="">Select day</option>
                  {DAYS_OF_WEEK.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm font-medium text-slate-700">
                Slot (0-{SLOTS_PER_DAY - 1})
                <input
                  type="number"
                  min={0}
                  max={SLOTS_PER_DAY - 1}
                  value={form.slot_index ?? ""}
                  onChange={(e) => update("slot_index", e.target.value === "" ? null : Number(e.target.value))}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
              </label>
            </div>
          )}

          {form.type === CommitmentType.RECURRING_QUOTA && (
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm font-medium text-slate-700">
                Target / week
                <input
                  type="number"
                  min={1}
                  value={form.target_per_week ?? ""}
                  onChange={(e) =>
                    update("target_per_week", e.target.value === "" ? null : Number(e.target.value))
                  }
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Preferred slot
                <input
                  type="number"
                  min={0}
                  max={SLOTS_PER_DAY - 1}
                  value={form.slot_index ?? ""}
                  onChange={(e) => update("slot_index", e.target.value === "" ? null : Number(e.target.value))}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
              </label>
            </div>
          )}

          {form.type === CommitmentType.HARD_DEADLINE && (
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm font-medium text-slate-700">
                Deadline day
                <select
                  value={form.deadline_day ?? ""}
                  onChange={(e) => update("deadline_day", (e.target.value || null) as DayOfWeek | null)}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="">Select day</option>
                  {DAYS_OF_WEEK.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm font-medium text-slate-700">
                Deadline slot
                <input
                  type="number"
                  min={0}
                  max={SLOTS_PER_DAY - 1}
                  value={form.deadline_slot ?? ""}
                  onChange={(e) =>
                    update("deadline_slot", e.target.value === "" ? null : Number(e.target.value))
                  }
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
              </label>
            </div>
          )}

          <div className="mt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            >
              {saving ? "Saving…" : editing ? "Save Changes" : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
