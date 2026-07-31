import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { backupApi, handleApiError } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type { RestoreBackupRequest } from "@/types/api";

interface BackupPageOptions {
  limit?: number;
  offset?: number;
}

export function useBackups(
  deviceMac: string | null | undefined,
  options?: BackupPageOptions,
) {
  const page = pageOf(options);
  return useQuery({
    queryKey: queryKeys.backups.list({
      scope: "device",
      deviceMac: deviceMac ?? null,
      ...page,
    }),
    queryFn: () =>
      backupApi.listBackups({ deviceMac: deviceMac ?? undefined, ...page }),
    enabled: !!deviceMac,
  });
}

export function useAllBackups(options?: BackupPageOptions) {
  const page = pageOf(options);
  return useQuery({
    queryKey: queryKeys.backups.list({ scope: "all", ...page }),
    queryFn: () => backupApi.listBackups(page),
  });
}

export function useBackup(backupId: number) {
  return useQuery({
    queryKey: queryKeys.backups.detail(backupId),
    queryFn: () => backupApi.getBackup(backupId),
  });
}

export function useCreateBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { deviceIp: string; name?: string }) =>
      backupApi.createBackup({ device_ip: params.deviceIp, name: params.name }),
    onSuccess: (backup) => {
      toast.success(`Backup #${backup.id} created`);
      queryClient.invalidateQueries({ queryKey: queryKeys.backups.all() });
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useDeleteBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (backupId: number) => backupApi.deleteBackup(backupId),
    onSuccess: (_data, backupId) => {
      toast.success("Backup deleted");
      queryClient.removeQueries({
        queryKey: queryKeys.backups.detail(backupId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.backups.all() });
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

function pageOf(options?: BackupPageOptions) {
  return {
    limit: options?.limit ?? 50,
    offset: options?.offset ?? 0,
  };
}
