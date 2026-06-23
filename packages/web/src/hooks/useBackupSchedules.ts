import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { backupScheduleApi, handleApiError } from "@/lib/api";
import type {
  CreateBackupScheduleRequest,
  UpdateBackupScheduleRequest,
} from "@/types/api";

const QUERY_KEY = ["backup-schedules"];

export function useBackupSchedules() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: backupScheduleApi.listSchedules,
  });
}

export function useCreateBackupSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateBackupScheduleRequest) =>
      backupScheduleApi.createSchedule(data),
    onSuccess: (schedule) => {
      toast.success(`Schedule "${schedule.name}" created`);
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useUpdateBackupSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { id: number; data: UpdateBackupScheduleRequest }) =>
      backupScheduleApi.updateSchedule(params.id, params.data),
    onSuccess: (schedule) => {
      toast.success(`Schedule "${schedule.name}" updated`);
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useDeleteBackupSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => backupScheduleApi.deleteSchedule(id),
    onSuccess: () => {
      toast.success("Schedule deleted");
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useSetScheduleEnabled() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { id: number; enabled: boolean }) =>
      backupScheduleApi.setEnabled(params.id, params.enabled),
    onSuccess: (schedule) => {
      toast.success(
        `Schedule "${schedule.name}" ${schedule.enabled ? "enabled" : "disabled"}`,
      );
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useRunBackupSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => backupScheduleApi.runSchedule(id),
    onSuccess: (result) => {
      const summary = `${result.ok} ok, ${result.failed} failed, ${result.skipped} skipped`;
      if (result.failed > 0) {
        toast.warning(`Run finished with issues: ${summary}`);
      } else {
        toast.success(`Run complete: ${summary}`);
      }
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}
