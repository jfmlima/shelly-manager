import { useQuery } from "@tanstack/react-query";

import { loadScanResults } from "@/lib/storage";
import type { Device } from "@/types/api";

/**
 * Read the devices from the most recent network scan.
 *
 * Shares the ["devices", "scan"] query key with the dashboard, so it reflects
 * whatever was last scanned (and never triggers a scan of its own).
 */
export function useScannedDevices() {
  return useQuery<Device[]>({
    queryKey: ["devices", "scan"],
    queryFn: () => {
      const cached = loadScanResults();
      return cached ? cached.devices : [];
    },
    staleTime: Infinity,
    gcTime: Infinity,
  });
}
