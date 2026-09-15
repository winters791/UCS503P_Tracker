import { useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { useAppState } from "../context/AppStateContext";
import type { DragPayload } from "../types/dnd";
import type { ScheduleSlot } from "../types/domain";
import { CommitmentSidebar } from "./CommitmentSidebar";
import { WeeklyGrid } from "./WeeklyGrid";
import { TYPE_STYLES } from "../utils/blockStyles";

interface PlannerBoardProps {
  onSelectBlock: (slot: ScheduleSlot) => void;
}

export function PlannerBoard({ onSelectBlock }: PlannerBoardProps) {
  const { grid, moveBlock, placeCommitment, reslotFlexible, mode } = useAppState();
  const [activeDrag, setActiveDrag] = useState<DragPayload | null>(null);
  const [overCellKey, setOverCellKey] = useState<string | null>(null);
  const [overIsCollision, setOverIsCollision] = useState(false);
  const [showReslotBanner, setShowReslotBanner] = useState(false);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  function handleDragStart(event: DragStartEvent) {
    setActiveDrag((event.active.data.current as DragPayload) ?? null);
  }

  function handleDragOver(event: DragOverEvent) {
    const over = event.over;
    const payload = event.active.data.current as DragPayload | undefined;
    if (!over || !grid || !payload) {
      setOverCellKey(null);
      return;
    }
    const key = over.id as string;
    setOverCellKey(key);
    const data = over.data.current as { day: string; slotIndex: number };
    const occupant = grid.slots.find(
      (s) => s.day_of_week === data.day && s.slot_index === data.slotIndex,
    );
    const isSameBlock = payload.kind === "block" && occupant?.block_id === payload.slot.block_id;
    setOverIsCollision(Boolean(occupant?.block_id) && !isSameBlock);
  }

  async function handleDragEnd(event: DragEndEvent) {
    setOverCellKey(null);
    const payload = activeDrag;
    setActiveDrag(null);
    const { over } = event;
    if (!over || !payload) return;

    const data = over.data.current as { day: ScheduleSlot["day_of_week"]; slotIndex: number };

    const result =
      payload.kind === "block"
        ? await moveBlock(payload.slot.block_id!, data.day, data.slotIndex)
        : await placeCommitment(payload.commitment.id, data.day, data.slotIndex);

    if (result.ok) setShowReslotBanner(true);
  }

  return (
    <div className="flex flex-col gap-3">
      {showReslotBanner && (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-violet-300 bg-violet-50 px-4 py-2 text-sm text-violet-900">
          <span>Re-run the solver to re-slot surrounding flexible tasks around this change?</span>
          <div className="flex gap-2 shrink-0">
            <button
              onClick={async () => {
                await reslotFlexible();
                setShowReslotBanner(false);
              }}
              disabled={mode === "reslotting"}
              className="rounded-md bg-violet-600 px-3 py-1 text-white text-xs font-medium hover:bg-violet-700 disabled:opacity-50"
            >
              {mode === "reslotting" ? "Re-slotting…" : "Re-slot flexible tasks"}
            </button>
            <button
              onClick={() => setShowReslotBanner(false)}
              className="rounded-md px-3 py-1 text-xs font-medium text-violet-700 hover:bg-violet-100"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      <DndContext
        sensors={sensors}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 items-start">
          <CommitmentSidebar />
          <div className="flex-1 min-w-0">
            <WeeklyGrid
              grid={grid}
              overCellKey={overCellKey}
              overIsCollision={overIsCollision}
              draggingBlockId={activeDrag?.kind === "block" ? activeDrag.slot.block_id : null}
              onSelectBlock={onSelectBlock}
            />
          </div>
        </div>

        <DragOverlay>
          {activeDrag &&
            (() => {
              const title =
                activeDrag.kind === "block" ? activeDrag.slot.commitment_title : activeDrag.commitment.title;
              const type =
                activeDrag.kind === "block" ? activeDrag.slot.commitment_type : activeDrag.commitment.type;
              if (!title || !type) return null;
              const style = TYPE_STYLES[type];
              return (
                <div
                  className={`rounded-md border px-2 py-1 text-[11px] font-medium shadow-lg ${style.bg} ${style.border} ${style.text}`}
                >
                  {title}
                </div>
              );
            })()}
        </DragOverlay>
      </DndContext>
    </div>
  );
}
