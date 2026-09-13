import { apiClient } from "./client";
import type { ExecutionLog, ExecutionLogCreate } from "../types/domain";

export const executionLogsApi = {
  create: async (payload: ExecutionLogCreate): Promise<ExecutionLog> => {
    const { data } = await apiClient.post<ExecutionLog>("/execution-logs", payload);
    return data;
  },
};
