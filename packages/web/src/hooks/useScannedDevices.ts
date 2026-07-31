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
      return deviceApi.scanDevices(params);
    },
    onSuccess: (devices, params) => {
      saveScanResults(devices, params);
      queryClient.setQueryData(queryKeys.devices.scan(), devices);
      toast.success(
        t("dashboard.messages.scanSuccess", { count: devices.length }),
      );
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}
