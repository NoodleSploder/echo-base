import { Outlet } from "react-router-dom";
import { EventToastBridge } from "../common/EventToastBridge";
import { ToastContainer } from "../common/ToastContainer";
import { EventStreamProvider } from "../../context/EventStreamContext";
import { ToastProvider } from "../../context/ToastContext";
import { BottomStatusBar } from "./BottomStatusBar";
import { TopNav } from "./TopNav";

export function AppShell() {
  return (
    <EventStreamProvider enabled>
      <ToastProvider>
        <div className="flex h-screen flex-col bg-base-950">
          <TopNav />
          <main className="flex-1 overflow-y-auto p-4">
            <Outlet />
          </main>
          <BottomStatusBar />
        </div>
        <EventToastBridge />
        <ToastContainer />
      </ToastProvider>
    </EventStreamProvider>
  );
}
