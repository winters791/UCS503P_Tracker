import { useMemo } from "react";
import { DAYS_OF_WEEK, SLOTS_PER_DAY } from "../types/domain";
import type { ScheduleGrid, ScheduleSlot } from "../types/domain";
import { GridCell } from "./GridCell";
import { BlockCard } from "./BlockCard";
import { slotLabel, cellKey } from "../utils/time";
import { TYPE_STYLES } from "../utils/blockStyles";

interface WeeklyGridProps {
  grid: ScheduleGrid | null;
  overCellKey: string | null;
  overIsCollision: boolean;
  draggingBlockId: string | null;
  onSelectBlock: (slot: ScheduleSlot) => void;
}

export function WeeklyGrid({ grid, overCellKey, overIsCollision, draggingBlockId, onSelectBlock }: WeeklyGridProps) {
  const slotsByKey = useMemo(() => {
    const map = new Map<string, ScheduleSlot>();
    grid?.slots.forEach((s) => map.set(cellKey(s.day_of_week, s.slot_index), s));
    return map;
  }, [grid]);

  if (!grid) {
    return <div className="p-8 text-center text-slate-500">Loading schedule…</div>;
  }

  return (
    <div className="flex flex-col gap-3">
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
                      {slot?.block_id && slot.block_id !== draggingBlockId && (
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
