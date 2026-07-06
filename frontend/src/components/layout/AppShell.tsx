import { Outlet } from "react-router-dom";
import { EventStreamProvider } from "../../context/EventStreamContext";
import { BottomStatusBar } from "./BottomStatusBar";
import { TopNav } from "./TopNav";

export function AppShell() {
  return (
    <EventStreamProvider enabled>
      <div className="flex h-screen flex-col bg-base-950">
        <TopNav />
        <main className="flex-1 overflow-y-auto p-4">
          <Outlet />
        </main>
        <BottomStatusBar />
      </div>
    </EventStreamProvider>
  );
}
