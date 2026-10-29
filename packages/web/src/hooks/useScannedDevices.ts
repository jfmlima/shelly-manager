import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { deviceApi, handleApiError } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import {
  clearScanResults,
  loadScanResults,
  saveScanResults,
} from "@/lib/storage";
import type { Device, ScanRequest } from "@/types/api";

const FAILED_SCAN_STATUSES = ["unreachable", "error"];

export function isScanFailure(device: Device): boolean {
  return FAILED_SCAN_STATUSES.includes(device.status);
}

export function useScannedDevices() {
  return useQuery<Device[]>({
    queryKey: queryKeys.devices.scan(),
    queryFn: () => {
      const cached = loadScanResults();
      return cached ? cached.devices : [];
    },
    staleTime: Infinity,
    gcTime: Infinity,
  });
}

export function useScanDevices() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: ScanRequest) => {
      clearScanResults();
      queryClient.removeQueries({ queryKey: queryKeys.devices.scan() });
      return deviceApi.scanDevices({ ...params, include_failed: true });
    },
    onSuccess: (results, params) => {
      // Only devices reach the cache: the backup schedule form offers the
      // cached list as targets, and a dead address must not be one of them.
      const devices = results.filter((device) => !isScanFailure(device));
      const failed = results.length - devices.length;
      saveScanResults(devices, params);
      queryClient.setQueryData(queryKeys.devices.scan(), devices);
      toast.success(
        failed > 0
          ? t("dashboard.messages.scanPartial", {
              count: devices.length,
              failed,
            })
          : t("dashboard.messages.scanSuccess", { count: devices.length }),
      );
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}
