import { apiClient } from "./client";
import type {
  ScheduleGrid,
  ScheduledBlock,
  ScheduledBlockCreate,
  ScheduledBlockUpdate,
} from "../types/domain";

export const scheduleApi = {
  get: async (): Promise<ScheduleGrid> => {
    const { data } = await apiClient.get<ScheduleGrid>("/schedule");
    return data;
  },
  reslotFlexible: async (): Promise<ScheduleGrid> => {
    const { data } = await apiClient.post<ScheduleGrid>("/schedule/reslot-flexible");
    return data;
  },
};

export const scheduledBlocksApi = {
  create: async (payload: ScheduledBlockCreate): Promise<ScheduledBlock> => {
    const { data } = await apiClient.post<ScheduledBlock>("/scheduled-blocks", payload);
    return data;
  },
  update: async (id: string, payload: ScheduledBlockUpdate): Promise<ScheduledBlock> => {
    const { data } = await apiClient.patch<ScheduledBlock>(`/scheduled-blocks/${id}`, payload);
    return data;
  },
};
