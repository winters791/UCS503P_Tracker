import { useEffect, useState } from "react";
import { insightsApi } from "../api/insights";
import { extractErrorMessage } from "../api/client";
import { useToast } from "../context/ToastContext";
import type { ConsistencyReport, RetrospectiveReport } from "../types/domain";
import { addDays } from "../utils/dates";
import { ConsistencyPanel } from "./ConsistencyPanel";
import { RetrospectivePanel } from "./RetrospectivePanel";

export function ReviewPage() {
  const { pushToast } = useToast();
  const [consistency, setConsistency] = useState<ConsistencyReport | null>(null);
  const [retro, setRetro] = useState<RetrospectiveReport | null>(null);
  // null = this week; otherwise the Monday of the week being reviewed
  const [weekStart, setWeekStart] = useState<string | null>(null);

  useEffect(() => {
    insightsApi
      .consistency()
      .then(setConsistency)
      .catch((err) => pushToast(extractErrorMessage(err), "error"));
  }, [pushToast]);

  useEffect(() => {
    insightsApi
      .retrospective(weekStart ?? undefined)
      .then(setRetro)
      .catch((err) => pushToast(extractErrorMessage(err), "error"));
  }, [weekStart, pushToast]);

  const currentWeek = consistency?.week_start ?? null;
  const shown = weekStart ?? currentWeek;
  const isCurrentWeek = weekStart === null || weekStart === currentWeek;

  function shift(days: number) {
    if (!shown) return;
    const next = addDays(shown, days);
    setRetro(null);
    setWeekStart(next === currentWeek ? null : next);
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] items-start">
      <ConsistencyPanel report={consistency} />
      <RetrospectivePanel
        report={retro}
        isCurrentWeek={isCurrentWeek}
        onPrevWeek={() => shift(-7)}
        onNextWeek={() => shift(7)}
      />
    </div>
  );
}
