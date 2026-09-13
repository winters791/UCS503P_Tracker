import { apiClient } from "./client";
import type { ScheduleGrid, ScheduledBlockUpdate, ScheduledBlock } from "../types/domain";

export const scheduleApi = {
  get: async (): Promise<ScheduleGrid> => {
    const { data } = await apiClient.get<ScheduleGrid>("/schedule");
    return data;
  },
  solve: async (): Promise<ScheduleGrid> => {
    const { data } = await apiClient.post<ScheduleGrid>("/schedule/solve");
    return data;
  },
  reslotFlexible: async (): Promise<ScheduleGrid> => {
    const { data } = await apiClient.post<ScheduleGrid>("/schedule/reslot-flexible");
    return data;
  },
};

export const scheduledBlocksApi = {
  update: async (id: string, payload: ScheduledBlockUpdate): Promise<ScheduledBlock> => {
    const { data } = await apiClient.patch<ScheduledBlock>(`/scheduled-blocks/${id}`, payload);
    return data;
  },
};
