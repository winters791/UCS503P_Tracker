import { apiClient } from "./client";
import type { Commitment, CommitmentCreate, CommitmentUpdate } from "../types/domain";

export const commitmentsApi = {
  list: async (): Promise<Commitment[]> => {
    const { data } = await apiClient.get<Commitment[]>("/commitments");
    return data;
  },
  create: async (payload: CommitmentCreate): Promise<Commitment> => {
    const { data } = await apiClient.post<Commitment>("/commitments", payload);
    return data;
  },
  update: async (id: string, payload: CommitmentUpdate): Promise<Commitment> => {
    const { data } = await apiClient.patch<Commitment>(`/commitments/${id}`, payload);
    return data;
  },
  remove: async (id: string): Promise<void> => {
    await apiClient.delete(`/commitments/${id}`);
  },
};
