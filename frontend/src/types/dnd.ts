import type { Commitment, ScheduleSlot } from "./domain";

export type DragPayload =
  | { kind: "block"; slot: ScheduleSlot }
  | { kind: "commitment"; commitment: Commitment };
