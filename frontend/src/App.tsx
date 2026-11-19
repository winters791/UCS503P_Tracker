import { useState } from "react";
import { AppStateProvider } from "./context/AppStateContext";
import { ToastProvider } from "./context/ToastContext";
import { ToastTray } from "./components/ToastTray";
import { Toolbar, type View } from "./components/Toolbar";
import { PlannerBoard } from "./components/PlannerBoard";
import { BlockDetailModal } from "./components/BlockDetailModal";
import { ReviewPage } from "./components/ReviewPage";
import type { ScheduleSlot } from "./types/domain";

function Dashboard() {
  const [selectedSlot, setSelectedSlot] = useState<ScheduleSlot | null>(null);
  const [view, setView] = useState<View>("planner");

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="mx-auto flex max-w-[1400px] flex-col gap-4">
        <Toolbar view={view} onChangeView={setView} />
        {view === "planner" ? <PlannerBoard onSelectBlock={setSelectedSlot} /> : <ReviewPage />}
      </div>

      {selectedSlot && (
        <BlockDetailModal slot={selectedSlot} onClose={() => setSelectedSlot(null)} />
      )}

      <ToastTray />
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppStateProvider>
        <Dashboard />
      </AppStateProvider>
    </ToastProvider>
  );
}
