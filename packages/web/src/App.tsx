import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";

import { ThemeProvider } from "@/components/theme-provider";
import { Layout } from "@/components/layout/layout";
import { Dashboard } from "@/pages/dashboard";
import { DeviceDetail } from "@/pages/device-detail";
import { Settings } from "@/pages/settings";
import { queryClient } from "@/lib/query-client";

// Initialize i18n
import "@/i18n";

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="system" storageKey="shelly-manager-theme">
        <Router>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="devices/:ip" element={<DeviceDetail />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
