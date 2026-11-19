import { CommitmentType, RuleType, type ConstraintRule } from "../types/domain";
import { slotLabel } from "./time";

export const TIME_BANDS = ["Morning", "Afternoon", "Evening"] as const;
export const DEFAULT_ENERGY_CUTOFF = 3;

export const RULE_TYPE_LABEL: Record<RuleType, string> = {
  [RuleType.TIME_OF_DAY_AFFINITY]: "Time of day",
  [RuleType.ENERGY_TIERING]: "High-focus hours",
  [RuleType.SEPARATION]: "Rest days between sessions",
};

/** Rule types that make sense for a commitment type (mirrors the API's validation). */
export function ruleTypesFor(type: CommitmentType): RuleType[] {
  if (type === CommitmentType.FIXED_EVENT) return [];
  const types: RuleType[] = [RuleType.TIME_OF_DAY_AFFINITY, RuleType.ENERGY_TIERING];
  if (type === CommitmentType.RECURRING_QUOTA) types.push(RuleType.SEPARATION);
  return types;
}

export function defaultTargetSlot(type: RuleType): number {
  if (type === RuleType.TIME_OF_DAY_AFFINITY) return 2;
  if (type === RuleType.ENERGY_TIERING) return DEFAULT_ENERGY_CUTOFF;
  return 1;
}

export function describeRule(rule: Pick<ConstraintRule, "rule_type" | "target_slot">): string {
  switch (rule.rule_type) {
    case RuleType.TIME_OF_DAY_AFFINITY:
      return `${TIME_BANDS[rule.target_slot ?? 0]} only`;
    case RuleType.ENERGY_TIERING:
      return `High focus, starts by ${slotLabel(rule.target_slot ?? DEFAULT_ENERGY_CUTOFF).start}`;
    case RuleType.SEPARATION: {
      const days = rule.target_slot ?? 1;
      return `${days} rest day${days === 1 ? "" : "s"} between`;
    }
  }
}
