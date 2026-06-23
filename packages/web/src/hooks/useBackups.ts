import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { backupApi, handleApiError } from "@/lib/api";
import type { RestoreBackupRequest } from "@/types/api";

export function useBackups(deviceMac: string | null | undefined) {
  return useQuery({
    queryKey: ["backups", deviceMac],
    queryFn: () => backupApi.listBackups(deviceMac ?? undefined),
    enabled: !!deviceMac,
  });
}

export function useCreateBackup(deviceMac: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { deviceIp: string; name?: string }) =>
      backupApi.createBackup({ device_ip: params.deviceIp, name: params.name }),
    onSuccess: (backup) => {
      toast.success(`Backup #${backup.id} created`);
      queryClient.invalidateQueries({ queryKey: ["backups", deviceMac] });
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useDeleteBackup(deviceMac: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (backupId: number) => backupApi.deleteBackup(backupId),
    onSuccess: () => {
      toast.success("Backup deleted");
      queryClient.invalidateQueries({ queryKey: ["backups", deviceMac] });
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useRestoreBackup() {
  return useMutation({
    mutationFn: (params: { backupId: number; data: RestoreBackupRequest }) =>
      backupApi.restoreBackup(params.backupId, params.data),
    onSuccess: (result) => {
      const summary = `${result.succeeded} ok, ${result.failed} failed, ${result.skipped} skipped`;
      if (result.success) {
        toast.success(`Restore complete: ${summary}`);
      } else {
        toast.warning(`Restore finished with issues: ${summary}`);
      }
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}
