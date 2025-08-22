import { useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { deviceApi, handleApiError } from "@/lib/api";
import type { Device } from "@/types/api";
import type { BulkProgress } from "../types";

interface UseBulkActionsProps {
  selectedDevices: Device[];
  onComplete?: () => void;
  setProgress: (
    value:
      | BulkProgress
      | null
      | ((prev: BulkProgress | null) => BulkProgress | null),
  ) => void;
}

export function useBulkActions({
  selectedDevices,
  onComplete,
  setProgress,
}: UseBulkActionsProps) {
  const { t } = useTranslation();

  const bulkUpdateMutation = useMutation({
    mutationFn: async (updateChannel: "stable" | "beta") => {
      const deviceIps = selectedDevices.map((device) => device.ip);
      return deviceApi.bulkExecuteOperation(deviceIps, "update", {
        channel: updateChannel,
      });
    },
    onSuccess: (results) => {
      const successful = results.filter((r) => r.success).length;
      const failed = results.filter((r) => !r.success).length;

      setProgress({
        total: results.length,
        completed: successful,
        failed,
        results,
        isRunning: false,
      });

      if (failed === 0) {
        toast.success(
          t("bulkActions.messages.updateSuccess", { count: successful }),
        );
      } else {
        toast.warning(
          t("bulkActions.messages.updatePartial", { successful, failed }),
        );
      }

      onComplete?.();
    },
    onError: (error) => {
      toast.error(handleApiError(error));
      setProgress((prev) => (prev ? { ...prev, isRunning: false } : null));
    },
  });

  const bulkRebootMutation = useMutation({
    mutationFn: async () => {
      const deviceIps = selectedDevices.map((device) => device.ip);
      return deviceApi.bulkExecuteOperation(deviceIps, "reboot");
    },
    onSuccess: (results) => {
      const successful = results.filter((r) => r.success).length;
      const failed = results.filter((r) => !r.success).length;

      setProgress({
        total: results.length,
        completed: successful,
        failed,
        results,
        isRunning: false,
      });

      if (failed === 0) {
        toast.success(
          t("bulkActions.messages.rebootSuccess", { count: successful }),
        );
      } else {
        toast.warning(
          t("bulkActions.messages.rebootPartial", { successful, failed }),
        );
      }

      onComplete?.();
    },
    onError: (error) => {
      toast.error(handleApiError(error));
      setProgress((prev) => (prev ? { ...prev, isRunning: false } : null));
    },
  });

  const bulkFactoryResetMutation = useMutation({
    mutationFn: async () => {
      const deviceIps = selectedDevices.map((device) => device.ip);
      return deviceApi.bulkExecuteOperation(deviceIps, "factory_reset");
    },
    onSuccess: (results) => {
      const successful = results.filter((r) => r.success).length;
      const failed = results.filter((r) => !r.success).length;

      setProgress({
        total: results.length,
        completed: successful,
        failed,
        results,
        isRunning: false,
      });

      if (failed === 0) {
        toast.success(
          t("bulkActions.messages.factoryResetSuccess", { count: successful }),
        );
      } else {
        toast.warning(
          t("bulkActions.messages.factoryResetPartial", { successful, failed }),
        );
      }

      onComplete?.();
    },
    onError: (error) => {
      toast.error(handleApiError(error));
      setProgress((prev) => (prev ? { ...prev, isRunning: false } : null));
    },
  });

  const bulkExportConfigMutation = useMutation({
    mutationFn: async (selectedComponentTypes: string[]) => {
      const deviceIps = selectedDevices.map((device) => device.ip);
      return deviceApi.bulkExportConfig(deviceIps, selectedComponentTypes);
    },
    onSuccess: (result) => {
      const blob = new Blob([JSON.stringify(result, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `shelly-config-export-${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      const deviceCount = Object.keys(result.devices || {}).length;
      toast.success(
        t("bulkActions.messages.exportSuccess", { count: deviceCount }),
      );

      setProgress({
        total: selectedDevices.length,
        completed: deviceCount,
        failed: selectedDevices.length - deviceCount,
        results: [],
        isRunning: false,
      });

      onComplete?.();
    },
    onError: (error) => {
      toast.error(handleApiError(error));
      setProgress((prev) => (prev ? { ...prev, isRunning: false } : null));
    },
  });

  const bulkApplyConfigMutation = useMutation({
    mutationFn: async ({
      selectedComponentType,
      configurationJson,
    }: {
      selectedComponentType: string;
      configurationJson: string;
    }) => {
      const deviceIps = selectedDevices.map((device) => device.ip);
      const config = JSON.parse(configurationJson);
      return deviceApi.bulkApplyConfig(
        deviceIps,
        selectedComponentType,
        config,
      );
    },
    onSuccess: (results) => {
      const successful = results.filter((r) => r.success).length;
      const failed = results.filter((r) => !r.success).length;

      setProgress({
        total: results.length,
        completed: successful,
        failed,
        results,
        isRunning: false,
      });

      if (failed === 0) {
        toast.success(
          t("bulkActions.messages.applySuccess", { count: successful }),
        );
      } else {
        toast.warning(
          t("bulkActions.messages.applyPartial", { successful, failed }),
        );
      }

      onComplete?.();
    },
    onError: (error) => {
      toast.error(handleApiError(error));
      setProgress((prev) => (prev ? { ...prev, isRunning: false } : null));
    },
  });

  return {
    bulkUpdateMutation,
    bulkRebootMutation,
    bulkFactoryResetMutation,
    bulkExportConfigMutation,
    bulkApplyConfigMutation,
  };
}
