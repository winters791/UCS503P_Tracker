import { useState } from "react";
import { AppStateProvider } from "./context/AppStateContext";
import { ToastProvider } from "./context/ToastContext";
import { ToastTray } from "./components/ToastTray";
import { Toolbar } from "./components/Toolbar";
import { CommitmentSidebar } from "./components/CommitmentSidebar";
import { WeeklyGrid } from "./components/WeeklyGrid";
import { BlockDetailModal } from "./components/BlockDetailModal";
import type { ScheduleSlot } from "./types/domain";

function Dashboard() {
  const [selectedSlot, setSelectedSlot] = useState<ScheduleSlot | null>(null);

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="mx-auto flex max-w-[1400px] flex-col gap-4">
        <Toolbar />
        <div className="flex gap-4 items-start">
          <CommitmentSidebar />
          <div className="flex-1 min-w-0">
            <WeeklyGrid onSelectBlock={setSelectedSlot} />
          </div>
        </div>
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
