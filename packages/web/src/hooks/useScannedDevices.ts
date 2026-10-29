import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { deviceApi, handleApiError } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import { isScanFailure, mergeScanResults } from "@/lib/scan-merge";
import {
  clearScanResults,
  loadScanResults,
  saveScanResults,
} from "@/lib/storage";
import type { Device, ScanRequest } from "@/types/api";

export { isScanFailure };

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
    mutationFn: (params: ScanRequest) =>
      deviceApi.scanDevices({ ...params, include_failed: true }),
    onSuccess: (results, params) => {
      // Failed addresses never enter the list on their own: the backup
      // schedule form offers the cached list as targets.
      const previous =
        queryClient.getQueryData<Device[]>(queryKeys.devices.scan()) ??
        loadScanResults()?.devices ??
        [];
      const devices = mergeScanResults(previous, results);
      const found = results.filter((device) => !isScanFailure(device)).length;
      const failed = results.length - found;
      saveScanResults(devices, params);
      queryClient.setQueryData(queryKeys.devices.scan(), devices);
      toast.success(
        failed > 0
          ? t("dashboard.messages.scanPartial", { count: found, failed })
          : t("dashboard.messages.scanSuccess", { count: found }),
      );
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useClearScanResults() {
  const queryClient = useQueryClient();
  return () => {
    clearScanResults();
    queryClient.setQueryData(queryKeys.devices.scan(), []);
  };
}
