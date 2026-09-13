import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import type { ScheduleSlot } from "../types/domain";
import { TYPE_STYLES, STATUS_STYLES } from "../utils/blockStyles";
import { COMMITMENT_TYPE_LABEL } from "../types/domain";

interface BlockCardProps {
  slot: ScheduleSlot;
  onClick: () => void;
}

export function BlockCard({ slot, onClick }: BlockCardProps) {
  const blockId = slot.block_id!;
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: blockId,
    data: { slot },
  });

  const style = transform
    ? { transform: CSS.Translate.toString(transform), zIndex: 50 }
    : undefined;

  const typeStyle = TYPE_STYLES[slot.commitment_type!];
  const statusStyle = slot.status ? STATUS_STYLES[slot.status] : "";

  return (
    <button
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={onClick}
      title={`${slot.commitment_title} (${COMMITMENT_TYPE_LABEL[slot.commitment_type!]})`}
      className={`w-full h-full rounded-md border px-1.5 py-1 text-left text-[11px] leading-tight overflow-hidden shadow-sm cursor-grab active:cursor-grabbing transition-opacity ${typeStyle.bg} ${typeStyle.border} ${typeStyle.text} ${statusStyle} ${isDragging ? "opacity-40" : ""}`}
    >
      <div className="flex items-center gap-1">
        <span className={`inline-block w-1.5 h-1.5 rounded-full ${typeStyle.dot}`} />
        <span className="font-medium truncate">{slot.commitment_title}</span>
      </div>
      {slot.status && slot.status !== "PLANNED" && (
        <div className="text-[9px] uppercase tracking-wide opacity-70">{slot.status}</div>
      )}
    </button>
  );
}
