import { apiClient } from "./client";
import type { ConstraintRule, ConstraintRuleCreate, ConstraintRuleWriteResult } from "../types/domain";

export const constraintRulesApi = {
  list: async (): Promise<ConstraintRule[]> => {
    const { data } = await apiClient.get<ConstraintRule[]>("/constraint-rules");
    return data;
  },
  create: async (payload: ConstraintRuleCreate): Promise<ConstraintRuleWriteResult> => {
    const { data } = await apiClient.post<ConstraintRuleWriteResult>("/constraint-rules", payload);
    return data;
  },
  remove: async (id: string): Promise<void> => {
    await apiClient.delete(`/constraint-rules/${id}`);
  },
};
