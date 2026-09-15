import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import type { Commitment } from "../types/domain";
import { COMMITMENT_TYPE_LABEL } from "../types/domain";
import { TYPE_STYLES } from "../utils/blockStyles";

interface DraggableCommitmentCardProps {
  commitment: Commitment;
  onEdit: () => void;
  onDelete: () => void;
}

export function DraggableCommitmentCard({ commitment, onEdit, onDelete }: DraggableCommitmentCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `commitment:${commitment.id}`,
    data: { kind: "commitment", commitment },
  });

  const style = transform ? { transform: CSS.Translate.toString(transform) } : undefined;
  const typeStyle = TYPE_STYLES[commitment.type];

  return (
    <li
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      title="Drag onto the timetable to schedule"
      className={`rounded-lg border px-3 py-2 text-sm cursor-grab active:cursor-grabbing touch-none ${typeStyle.bg} ${typeStyle.border} ${isDragging ? "opacity-40" : ""}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className={`font-medium truncate ${typeStyle.text}`}>{commitment.title}</p>
          <p className="text-[11px] text-slate-600">{COMMITMENT_TYPE_LABEL[commitment.type]}</p>
        </div>
        <div className="flex gap-1 shrink-0">
          <button
            onPointerDown={(e) => e.stopPropagation()}
            onClick={onEdit}
            className="text-[11px] font-medium text-slate-600 hover:text-slate-900"
          >
            Edit
          </button>
          <button
            onPointerDown={(e) => e.stopPropagation()}
            onClick={onDelete}
            className="text-[11px] font-medium text-red-600 hover:text-red-800"
          >
            Delete
          </button>
        </div>
      </div>
    </li>
  );
}
