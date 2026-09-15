import { useState } from "react";
import { useAppState } from "../context/AppStateContext";
import type { Commitment } from "../types/domain";
import { CommitmentFormModal } from "./CommitmentFormModal";
import { DraggableCommitmentCard } from "./DraggableCommitmentCard";

export function CommitmentSidebar() {
  const { commitments, deleteCommitment, loadingCommitments } = useAppState();
  const [editing, setEditing] = useState<Commitment | null>(null);
  const [showModal, setShowModal] = useState(false);

  function openCreate() {
    setEditing(null);
    setShowModal(true);
  }

  function openEdit(c: Commitment) {
    setEditing(c);
    setShowModal(true);
  }

  return (
    <aside className="w-80 shrink-0 rounded-xl border border-slate-200 bg-white p-4 flex flex-col gap-3 h-fit">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-900">Commitments</h2>
        <button
          onClick={openCreate}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800"
        >
          + New
        </button>
      </div>

      {loadingCommitments && <p className="text-xs text-slate-400">Loading…</p>}
      {!loadingCommitments && commitments.length === 0 && (
        <p className="text-xs text-slate-400">No commitments yet. Add one to get started.</p>
      )}
      {!loadingCommitments && commitments.length > 0 && (
        <p className="text-[11px] text-slate-400">Drag a commitment onto the timetable to schedule it.</p>
      )}

      <ul className="flex flex-col gap-2 max-h-[60vh] overflow-y-auto">
        {commitments.map((c) => (
          <DraggableCommitmentCard
            key={c.id}
            commitment={c}
            onEdit={() => openEdit(c)}
            onDelete={() => deleteCommitment(c.id)}
          />
        ))}
      </ul>

      {showModal && (
        <CommitmentFormModal editing={editing} onClose={() => setShowModal(false)} />
      )}
    </aside>
  );
}
