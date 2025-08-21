import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import type { Query } from "@tanstack/react-query";

import { ThemeProvider } from "@/components/theme-provider";
import { Layout } from "@/components/layout/layout";
import { Dashboard } from "@/pages/dashboard";
import { DeviceDetail } from "@/pages/device-detail";
import { Settings } from "@/pages/settings";
import { queryClient, persister } from "@/lib/query-client";

import "@/i18n";

function App() {
  return (
    <PersistQueryClientProvider
      client={queryClient}
      persistOptions={{
        persister,
        maxAge: 1000 * 60 * 60 * 24 * 7, // 7 days (longer than our 2-day stale threshold)
        dehydrateOptions: {
          shouldDehydrateQuery: (query: Query) => {
            return (
              query.queryKey.length >= 2 &&
              query.queryKey[0] === "devices" &&
              query.queryKey[1] === "scan" &&
              query.state.data !== undefined
            );
          },
        },
      }}
    >
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
    </PersistQueryClientProvider>
  );
}

export default App;
