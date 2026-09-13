import { useMemo, useState } from "react";
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
import { DAYS_OF_WEEK, SLOTS_PER_DAY } from "../types/domain";
import type { ScheduleSlot } from "../types/domain";
import { GridCell } from "./GridCell";
import { BlockCard } from "./BlockCard";
import { slotLabel, cellKey } from "../utils/time";
import { TYPE_STYLES } from "../utils/blockStyles";

interface WeeklyGridProps {
  onSelectBlock: (slot: ScheduleSlot) => void;
}

export function WeeklyGrid({ onSelectBlock }: WeeklyGridProps) {
  const { grid, moveBlock, reslotFlexible, mode } = useAppState();
  const [activeSlot, setActiveSlot] = useState<ScheduleSlot | null>(null);
  const [overCellKey, setOverCellKey] = useState<string | null>(null);
  const [overIsCollision, setOverIsCollision] = useState(false);
  const [showReslotBanner, setShowReslotBanner] = useState(false);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  const slotsByKey = useMemo(() => {
    const map = new Map<string, ScheduleSlot>();
    grid?.slots.forEach((s) => map.set(cellKey(s.day_of_week, s.slot_index), s));
    return map;
  }, [grid]);

  function handleDragStart(event: DragStartEvent) {
    setActiveSlot((event.active.data.current?.slot as ScheduleSlot) ?? null);
  }

  function handleDragOver(event: DragOverEvent) {
    const over = event.over;
    if (!over) {
      setOverCellKey(null);
      return;
    }
    const key = over.id as string;
    setOverCellKey(key);
    const occupant = slotsByKey.get(key);
    const activeId = event.active.id;
    setOverIsCollision(Boolean(occupant?.block_id && occupant.block_id !== activeId));
  }

  async function handleDragEnd(event: DragEndEvent) {
    setOverCellKey(null);
    setActiveSlot(null);
    const { active, over } = event;
    if (!over) return;

    const data = over.data.current as { day: string; slotIndex: number };
    const blockId = active.id as string;
    const result = await moveBlock(blockId, data.day as ScheduleSlot["day_of_week"], data.slotIndex);
    if (result.ok) {
      setShowReslotBanner(true);
    }
  }

  if (!grid) {
    return <div className="p-8 text-center text-slate-500">Loading schedule…</div>;
  }

  return (
    <div className="flex flex-col gap-3">
      {showReslotBanner && (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-violet-300 bg-violet-50 px-4 py-2 text-sm text-violet-900">
          <span>
            Block moved. Re-run the solver to re-slot surrounding flexible tasks around this change?
          </span>
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
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-slate-50 p-3">
          <div
            className="grid gap-1 min-w-[900px]"
            style={{ gridTemplateColumns: `72px repeat(${DAYS_OF_WEEK.length}, 1fr)` }}
          >
            <div />
            {DAYS_OF_WEEK.map((day) => (
              <div key={day} className="text-center text-xs font-semibold text-slate-600 pb-1">
                {day.slice(0, 3)}
              </div>
            ))}

            {Array.from({ length: SLOTS_PER_DAY }).map((_, slotIndex) => {
              const { start, end } = slotLabel(slotIndex);
              return (
                <div key={`row-${slotIndex}`} className="contents">
                  <div className="flex flex-col justify-center items-end pr-2 text-[10px] text-slate-500 leading-tight">
                    <span>{start}</span>
                    <span>{end}</span>
                  </div>
                  {DAYS_OF_WEEK.map((day) => {
                    const key = cellKey(day, slotIndex);
                    const slot = slotsByKey.get(key);
                    const occupied = Boolean(slot?.block_id);
                    return (
                      <GridCell
                        key={key}
                        day={day}
                        slotIndex={slotIndex}
                        isOccupied={occupied}
                        isCollision={overCellKey === key && overIsCollision}
                      >
                        {slot?.block_id && slot.block_id !== activeSlot?.block_id && (
                          <BlockCard slot={slot} onClick={() => onSelectBlock(slot)} />
                        )}
                      </GridCell>
                    );
                  })}
                  {slotIndex < SLOTS_PER_DAY - 1 && (
                    <div className="contents">
                      <div />
                      {DAYS_OF_WEEK.map((day) => (
                        <div
                          key={`buffer-${day}-${slotIndex}`}
                          className="h-1.5 mx-1 rounded-full bg-slate-200"
                          title="10-minute transition buffer"
                        />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <DragOverlay>
          {activeSlot?.commitment_type && (
            <div
              className={`rounded-md border px-2 py-1 text-[11px] font-medium shadow-lg ${TYPE_STYLES[activeSlot.commitment_type].bg} ${TYPE_STYLES[activeSlot.commitment_type].border} ${TYPE_STYLES[activeSlot.commitment_type].text}`}
            >
              {activeSlot.commitment_title}
            </div>
          )}
        </DragOverlay>
      </DndContext>

      <div className="flex flex-wrap gap-4 text-xs text-slate-600">
        {Object.entries(TYPE_STYLES).map(([type, style]) => (
          <div key={type} className="flex items-center gap-1.5">
            <span className={`inline-block w-2.5 h-2.5 rounded-full ${style.dot}`} />
            <span>{type.replace("_", " ")}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
