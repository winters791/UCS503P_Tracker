import { useState } from "react";
import { useAppState } from "../context/AppStateContext";
import { COMMITMENT_TYPE_LABEL, type Commitment } from "../types/domain";
import { TYPE_STYLES } from "../utils/blockStyles";
import { CommitmentFormModal } from "./CommitmentFormModal";

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

      <ul className="flex flex-col gap-2 max-h-[60vh] overflow-y-auto">
        {commitments.map((c) => {
          const style = TYPE_STYLES[c.type];
          return (
            <li
              key={c.id}
              className={`rounded-lg border px-3 py-2 text-sm ${style.bg} ${style.border}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className={`font-medium truncate ${style.text}`}>{c.title}</p>
                  <p className="text-[11px] text-slate-600">{COMMITMENT_TYPE_LABEL[c.type]}</p>
                </div>
                <div className="flex gap-1 shrink-0">
                  <button
                    onClick={() => openEdit(c)}
                    className="text-[11px] font-medium text-slate-600 hover:text-slate-900"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => deleteCommitment(c.id)}
                    className="text-[11px] font-medium text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </li>
          );
        })}
      </ul>

      {showModal && (
        <CommitmentFormModal editing={editing} onClose={() => setShowModal(false)} />
      )}
    </aside>
  );
}
