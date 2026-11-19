import { apiClient } from "./client";
import type { ConsistencyReport, RetrospectiveReport } from "../types/domain";

export const insightsApi = {
  consistency: async (): Promise<ConsistencyReport> => {
    const { data } = await apiClient.get<ConsistencyReport>("/insights/consistency");
    return data;
  },
  retrospective: async (weekStart?: string): Promise<RetrospectiveReport> => {
    const { data } = await apiClient.get<RetrospectiveReport>("/insights/retrospective", {
      params: weekStart ? { week_start: weekStart } : undefined,
    });
    return data;
  },
};
