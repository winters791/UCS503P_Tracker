import { CommitmentType, BlockStatus } from "../types/domain";

export const TYPE_STYLES: Record<CommitmentType, { bg: string; border: string; text: string; dot: string }> = {
  [CommitmentType.FIXED_EVENT]: {
    bg: "bg-blue-100",
    border: "border-blue-400",
    text: "text-blue-900",
    dot: "bg-blue-500",
  },
  [CommitmentType.RECURRING_QUOTA]: {
    bg: "bg-emerald-100",
    border: "border-emerald-400",
    text: "text-emerald-900",
    dot: "bg-emerald-500",
  },
  [CommitmentType.HARD_DEADLINE]: {
    bg: "bg-orange-100",
    border: "border-orange-400",
    text: "text-orange-900",
    dot: "bg-orange-500",
  },
  [CommitmentType.FLEXIBLE_TASK]: {
    bg: "bg-violet-100",
    border: "border-violet-400",
    text: "text-violet-900",
    dot: "bg-violet-500",
  },
};

export const STATUS_STYLES: Record<BlockStatus, string> = {
  [BlockStatus.PLANNED]: "",
  [BlockStatus.COMPLETED]: "ring-2 ring-emerald-500",
  [BlockStatus.MISSED]: "ring-2 ring-red-500 opacity-70",
  [BlockStatus.SKIPPED]: "ring-2 ring-slate-400 opacity-50",
};
