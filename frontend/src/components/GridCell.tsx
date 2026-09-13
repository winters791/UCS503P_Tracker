import { useDroppable } from "@dnd-kit/core";
import type { ReactNode } from "react";
import type { DayOfWeek } from "../types/domain";
import { cellKey } from "../utils/time";

interface GridCellProps {
  day: DayOfWeek;
  slotIndex: number;
  isOccupied: boolean;
  isCollision: boolean;
  children: ReactNode;
}

export function GridCell({ day, slotIndex, isOccupied, isCollision, children }: GridCellProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: cellKey(day, slotIndex),
    data: { day, slotIndex, isOccupied },
  });

  const highlight = isOver
    ? isCollision
      ? "bg-red-100 border-red-400"
      : "bg-emerald-50 border-emerald-400"
    : "border-slate-200";

  return (
    <div
      ref={setNodeRef}
      className={`relative h-14 border rounded-md p-0.5 bg-white transition-colors ${highlight}`}
    >
      {children}
    </div>
  );
}
