import { useState } from "react";
import { useAppState } from "../context/AppStateContext";
import { BlockStatus, COMMITMENT_TYPE_LABEL, type ScheduleSlot } from "../types/domain";
import { slotLabel } from "../utils/time";

interface BlockDetailModalProps {
  slot: ScheduleSlot;
  onClose: () => void;
}

export function BlockDetailModal({ slot, onClose }: BlockDetailModalProps) {
  const { logExecution, setBlockStatus } = useAppState();
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const { start, end } = slotLabel(slot.slot_index);

  async function logAs(completed: boolean) {
    if (!slot.block_id) return;
    setSaving(true);
    const ok = await logExecution({ block_id: slot.block_id, completed, notes: notes || null });
    setSaving(false);
    if (ok) onClose();
  }

  async function markSkipped() {
    if (!slot.block_id) return;
    setSaving(true);
    await setBlockStatus(slot.block_id, BlockStatus.SKIPPED);
    setSaving(false);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-900">{slot.commitment_title}</h2>
        <p className="text-xs text-slate-500 mb-4">
          {COMMITMENT_TYPE_LABEL[slot.commitment_type!]} · {slot.day_of_week} · {start}–{end}
          {slot.status && <> · currently {slot.status}</>}
        </p>

        <label className="text-sm font-medium text-slate-700 block mb-4">
          Reflection notes
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="What happened during this block?"
          />
        </label>

        <div className="flex flex-wrap gap-2">
          <button
            disabled={saving}
            onClick={() => logAs(true)}
            className="rounded-md bg-emerald-600 px-3 py-2 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            Mark Completed
          </button>
          <button
            disabled={saving}
            onClick={() => logAs(false)}
            className="rounded-md bg-red-600 px-3 py-2 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
          >
            Mark Missed
          </button>
          <button
            disabled={saving}
            onClick={markSkipped}
            className="rounded-md bg-slate-200 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-300 disabled:opacity-50"
          >
            Skip
          </button>
        </div>

        <div className="mt-4 flex justify-end">
          <button onClick={onClose} className="text-sm font-medium text-slate-500 hover:text-slate-800">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
