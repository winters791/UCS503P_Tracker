import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { commitmentsApi } from "../api/commitments";
import { scheduleApi, scheduledBlocksApi } from "../api/schedule";
import { executionLogsApi } from "../api/executionLogs";
import { extractErrorMessage } from "../api/client";
import { useToast } from "./ToastContext";
import type {
  Commitment,
  CommitmentCreate,
  CommitmentUpdate,
  DayOfWeek,
  ExecutionLogCreate,
  ScheduleGrid,
  ScheduleSlot,
} from "../types/domain";
import { BlockStatus } from "../types/domain";

export type InteractionMode = "idle" | "dragging" | "reslotting";

interface ActionResult {
  ok: boolean;
}

const EMPTY_SLOT_FIELDS: Omit<ScheduleSlot, "day_of_week" | "slot_index"> = {
  block_id: null,
  commitment_id: null,
  commitment_title: null,
  commitment_type: null,
  status: null,
};

interface AppStateValue {
  commitments: Commitment[];
  grid: ScheduleGrid | null;
  loadingCommitments: boolean;
  loadingGrid: boolean;
  mode: InteractionMode;
  refreshAll: () => Promise<void>;
  createCommitment: (payload: CommitmentCreate) => Promise<boolean>;
  updateCommitment: (id: string, payload: CommitmentUpdate) => Promise<boolean>;
  deleteCommitment: (id: string) => Promise<boolean>;
  reslotFlexible: () => Promise<void>;
  moveBlock: (blockId: string, day: DayOfWeek, slotIndex: number) => Promise<ActionResult>;
  placeCommitment: (commitmentId: string, day: DayOfWeek, slotIndex: number) => Promise<ActionResult>;
  setBlockStatus: (blockId: string, status: BlockStatus) => Promise<void>;
  logExecution: (payload: ExecutionLogCreate) => Promise<boolean>;
}

const AppStateContext = createContext<AppStateValue | null>(null);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const { pushToast } = useToast();
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [grid, setGrid] = useState<ScheduleGrid | null>(null);
  const [loadingCommitments, setLoadingCommitments] = useState(false);
  const [loadingGrid, setLoadingGrid] = useState(false);
  const [mode, setMode] = useState<InteractionMode>("idle");

  const refreshCommitments = useCallback(async () => {
    setLoadingCommitments(true);
    try {
      setCommitments(await commitmentsApi.list());
    } catch (err) {
      pushToast(extractErrorMessage(err), "error");
    } finally {
      setLoadingCommitments(false);
    }
  }, [pushToast]);

  const refreshGrid = useCallback(async () => {
    setLoadingGrid(true);
    try {
      setGrid(await scheduleApi.get());
    } catch (err) {
      pushToast(extractErrorMessage(err), "error");
    } finally {
      setLoadingGrid(false);
    }
  }, [pushToast]);

  const refreshAll = useCallback(async () => {
    await Promise.all([refreshCommitments(), refreshGrid()]);
  }, [refreshCommitments, refreshGrid]);

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const createCommitment = useCallback(
    async (payload: CommitmentCreate) => {
      try {
        await commitmentsApi.create(payload);
        await refreshCommitments();
        pushToast(`Created "${payload.title}"`, "success");
        return true;
      } catch (err) {
        pushToast(extractErrorMessage(err), "error");
        return false;
      }
    },
    [refreshCommitments, pushToast],
  );

  const updateCommitment = useCallback(
    async (id: string, payload: CommitmentUpdate) => {
      try {
        await commitmentsApi.update(id, payload);
        await refreshCommitments();
        pushToast("Commitment updated", "success");
        return true;
      } catch (err) {
        pushToast(extractErrorMessage(err), "error");
        return false;
      }
    },
    [refreshCommitments, pushToast],
  );

  const deleteCommitment = useCallback(
    async (id: string) => {
      try {
        await commitmentsApi.remove(id);
        await refreshAll();
        pushToast("Commitment deleted", "success");
        return true;
      } catch (err) {
        pushToast(extractErrorMessage(err), "error");
        return false;
      }
    },
    [refreshAll, pushToast],
  );

  const reslotFlexible = useCallback(async () => {
    setMode("reslotting");
    try {
      const result = await scheduleApi.reslotFlexible();
      setGrid(result);
      pushToast("Flexible tasks re-slotted around your change", "success");
    } catch (err) {
      pushToast(extractErrorMessage(err), "error");
    } finally {
      setMode("idle");
    }
  }, [pushToast]);

  const moveBlock = useCallback(
    async (blockId: string, day: DayOfWeek, slotIndex: number): Promise<ActionResult> => {
      if (!grid) return { ok: false };

      const moving = grid.slots.find((s) => s.block_id === blockId);
      if (!moving) return { ok: false };
      if (moving.day_of_week === day && moving.slot_index === slotIndex) return { ok: true };

      const targetOccupant = grid.slots.find(
        (s) => s.day_of_week === day && s.slot_index === slotIndex,
      );
      if (targetOccupant?.block_id && targetOccupant.block_id !== blockId) {
        pushToast(
          `Slot conflict: ${targetOccupant.commitment_title ?? "another block"} is already there`,
          "error",
        );
        return { ok: false };
      }

      const previousGrid = grid;
      // Swap cell *contents* between the source and target coordinates —
      // each ScheduleSlot's own day_of_week/slot_index is the cell's fixed
      // identity, so those fields must never change, only what occupies it.
      const optimistic: ScheduleGrid = {
        ...grid,
        slots: grid.slots.map((s) => {
          if (s.day_of_week === moving.day_of_week && s.slot_index === moving.slot_index) {
            return { day_of_week: s.day_of_week, slot_index: s.slot_index, ...EMPTY_SLOT_FIELDS };
          }
          if (s.day_of_week === day && s.slot_index === slotIndex) {
            return {
              day_of_week: s.day_of_week,
              slot_index: s.slot_index,
              block_id: moving.block_id,
              commitment_id: moving.commitment_id,
              commitment_title: moving.commitment_title,
              commitment_type: moving.commitment_type,
              status: moving.status,
            };
          }
          return s;
        }),
      };
      setGrid(optimistic);

      try {
        await scheduledBlocksApi.update(blockId, { day_of_week: day, slot_index: slotIndex });
        return { ok: true };
      } catch (err) {
        setGrid(previousGrid);
        pushToast(extractErrorMessage(err), "error");
        return { ok: false };
      }
    },
    [grid, pushToast],
  );

  const placeCommitment = useCallback(
    async (commitmentId: string, day: DayOfWeek, slotIndex: number): Promise<ActionResult> => {
      if (!grid) return { ok: false };

      const targetOccupant = grid.slots.find(
        (s) => s.day_of_week === day && s.slot_index === slotIndex,
      );
      if (targetOccupant?.block_id) {
        pushToast(
          `Slot conflict: ${targetOccupant.commitment_title ?? "another block"} is already there`,
          "error",
        );
        return { ok: false };
      }

      const commitment = commitments.find((c) => c.id === commitmentId);
      if (!commitment) return { ok: false };

      try {
        const block = await scheduledBlocksApi.create({
          commitment_id: commitmentId,
          day_of_week: day,
          slot_index: slotIndex,
        });
        setGrid((prev) =>
          prev
            ? {
                ...prev,
                slots: prev.slots.map((s) =>
                  s.day_of_week === day && s.slot_index === slotIndex
                    ? {
                        day_of_week: s.day_of_week,
                        slot_index: s.slot_index,
                        block_id: block.id,
                        commitment_id: commitment.id,
                        commitment_title: commitment.title,
                        commitment_type: commitment.type,
                        status: block.status,
                      }
                    : s,
                ),
              }
            : prev,
        );
        pushToast(`Scheduled "${commitment.title}"`, "success");
        return { ok: true };
      } catch (err) {
        pushToast(extractErrorMessage(err), "error");
        return { ok: false };
      }
    },
    [grid, commitments, pushToast],
  );

  const setBlockStatus = useCallback(
    async (blockId: string, status: BlockStatus) => {
      try {
        await scheduledBlocksApi.update(blockId, { status });
        await refreshGrid();
      } catch (err) {
        pushToast(extractErrorMessage(err), "error");
      }
    },
    [refreshGrid, pushToast],
  );

  const logExecution = useCallback(
    async (payload: ExecutionLogCreate) => {
      try {
        await executionLogsApi.create(payload);
        await setBlockStatus(payload.block_id, payload.completed ? BlockStatus.COMPLETED : BlockStatus.MISSED);
        pushToast("Execution log saved", "success");
        return true;
      } catch (err) {
        pushToast(extractErrorMessage(err), "error");
        return false;
      }
    },
    [pushToast, setBlockStatus],
  );

  const value = useMemo<AppStateValue>(
    () => ({
      commitments,
      grid,
      loadingCommitments,
      loadingGrid,
      mode,
      refreshAll,
      createCommitment,
      updateCommitment,
      deleteCommitment,
      reslotFlexible,
      moveBlock,
      placeCommitment,
      setBlockStatus,
      logExecution,
    }),
    [
      commitments,
      grid,
      loadingCommitments,
      loadingGrid,
      mode,
      refreshAll,
      createCommitment,
      updateCommitment,
      deleteCommitment,
      reslotFlexible,
      moveBlock,
      placeCommitment,
      setBlockStatus,
      logExecution,
    ],
  );

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}

export function useAppState() {
  const ctx = useContext(AppStateContext);
  if (!ctx) throw new Error("useAppState must be used within AppStateProvider");
  return ctx;
}
