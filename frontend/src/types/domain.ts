// Mirrors code/app/models.py, code/app/db_models.py, and code/app/schemas.py

export const CommitmentType = {
  FIXED_EVENT: "FIXED_EVENT",
  RECURRING_QUOTA: "RECURRING_QUOTA",
  FLEXIBLE_TASK: "FLEXIBLE_TASK",
  HARD_DEADLINE: "HARD_DEADLINE",
} as const;
export type CommitmentType = (typeof CommitmentType)[keyof typeof CommitmentType];

export const DayOfWeek = {
  MONDAY: "Monday",
  TUESDAY: "Tuesday",
  WEDNESDAY: "Wednesday",
  THURSDAY: "Thursday",
  FRIDAY: "Friday",
  SATURDAY: "Saturday",
  SUNDAY: "Sunday",
} as const;
export type DayOfWeek = (typeof DayOfWeek)[keyof typeof DayOfWeek];

export const BlockStatus = {
  PLANNED: "PLANNED",
  COMPLETED: "COMPLETED",
  MISSED: "MISSED",
  SKIPPED: "SKIPPED",
} as const;
export type BlockStatus = (typeof BlockStatus)[keyof typeof BlockStatus];

export const DAYS_OF_WEEK: DayOfWeek[] = [
  DayOfWeek.MONDAY,
  DayOfWeek.TUESDAY,
  DayOfWeek.WEDNESDAY,
  DayOfWeek.THURSDAY,
  DayOfWeek.FRIDAY,
  DayOfWeek.SATURDAY,
  DayOfWeek.SUNDAY,
];

export const SLOTS_PER_DAY = 12;

export interface Commitment {
  id: string;
  title: string;
  type: CommitmentType;
  target_per_week: number | null;
  duration_blocks: number;
  priority: number;
  day: DayOfWeek | null;
  slot_index: number | null;
  deadline_day: DayOfWeek | null;
  deadline_slot: number | null;
}

export type CommitmentCreate = Omit<Commitment, "id">;
export type CommitmentUpdate = Partial<CommitmentCreate>;

export interface ScheduledBlock {
  id: string;
  commitment_id: string;
  slot_index: number;
  day_of_week: DayOfWeek;
  status: BlockStatus;
  actual_start: string | null;
}

export type ScheduledBlockUpdate = Partial<
  Pick<ScheduledBlock, "slot_index" | "day_of_week" | "status" | "actual_start">
>;

export interface TimeSlot {
  day: DayOfWeek;
  slot_index: number;
  occupied_by: string | null;
}

export interface ScheduleSlot {
  day_of_week: DayOfWeek;
  slot_index: number;
  block_id: string | null;
  commitment_id: string | null;
  commitment_title: string | null;
  commitment_type: CommitmentType | null;
  status: BlockStatus | null;
}

export interface ScheduleGrid {
  slots: ScheduleSlot[];
  warnings: string[];
}

export interface ExecutionLog {
  id: string;
  block_id: string;
  completed: boolean;
  notes: string | null;
  logged_at: string;
}

export type ExecutionLogCreate = Omit<ExecutionLog, "id" | "logged_at">;
export type ExecutionLogUpdate = Partial<Pick<ExecutionLog, "completed" | "notes">>;

export const COMMITMENT_TYPE_LABEL: Record<CommitmentType, string> = {
  [CommitmentType.FIXED_EVENT]: "Fixed Event",
  [CommitmentType.RECURRING_QUOTA]: "Recurring Quota",
  [CommitmentType.FLEXIBLE_TASK]: "Flexible Task",
  [CommitmentType.HARD_DEADLINE]: "Hard Deadline",
};
