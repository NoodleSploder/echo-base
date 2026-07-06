import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/common/ProtectedRoute";
import { AppShell } from "./components/layout/AppShell";
import { ComingSoonPage } from "./pages/ComingSoonPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { ReceiversPage } from "./pages/ReceiversPage";
import { SatellitesPage } from "./pages/SatellitesPage";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="receivers" element={<ReceiversPage />} />
        <Route path="spectrum" element={<ComingSoonPage title="Spectrum Intelligence" phase="Phase 4" />} />
        <Route path="digital-modes" element={<ComingSoonPage title="Digital Modes" phase="Phase 5" />} />
        <Route path="messaging" element={<ComingSoonPage title="Messaging Center" phase="Phase 5" />} />
        <Route path="map" element={<ComingSoonPage title="Map" phase="Phase 9" />} />
        <Route path="satellites" element={<SatellitesPage />} />
        <Route path="alerts" element={<ComingSoonPage title="Alerts" phase="Phase 11" />} />
        <Route path="logs" element={<ComingSoonPage title="Logs" phase="Phase 1 (remaining: /api/system/logs)" />} />
        <Route path="system" element={<ComingSoonPage title="System" phase="Phase 1" />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
