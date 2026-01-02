import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { ScanForm } from "@/components/dashboard/scan-form";
import { DeviceTable } from "@/components/dashboard/device-table";
import { BulkActionsDialog } from "@/components/dashboard/bulk-actions-dialog";
import { Footer } from "@/components/ui/footer";
import { deviceApi, handleApiError } from "@/lib/api";
import {
  loadScanResults,
  saveScanResults,
  clearScanResults,
} from "@/lib/storage";
import type { Device, ScanRequest } from "@/types/api";

export function Dashboard() {
  const { t } = useTranslation();
  const [selectedDevices, setSelectedDevices] = useState<Device[]>([]);
  const [bulkActionsOpen, setBulkActionsOpen] = useState(false);
  const queryClient = useQueryClient();

  const {
    data: devices = [],
    isLoading: isLoadingCached,
    error: cacheError,
  } = useQuery({
    queryKey: ["devices", "scan"],
    queryFn: () => {
      const cached = loadScanResults();
      return cached ? cached.devices : [];
    },
    staleTime: Infinity, // Cached data never becomes stale automatically
    gcTime: Infinity, // Keep in memory indefinitely
    enabled: true, // Auto-load on mount
  });

  const scanMutation = useMutation({
    mutationFn: async (params: ScanRequest) => {
      clearScanResults();
      queryClient.removeQueries({ queryKey: ["devices", "scan"] });
      return deviceApi.scanDevices(params);
    },
    onSuccess: (data, variables) => {
      saveScanResults(data, variables);
      queryClient.setQueryData(["devices", "scan"], data);
      toast.success(
        t("dashboard.messages.scanSuccess", { count: data.length }),
      );
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  const handleScan = (request: ScanRequest) => {
    scanMutation.mutate(request);
  };

  const handleBulkAction = (devices: Device[]) => {
    setSelectedDevices(devices);
    setBulkActionsOpen(true);
  };

  const handleBulkActionComplete = () => {
    // refetch();
  };

  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col">
      {/* Main Content */}
      <div className="flex-1 space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {t("dashboard.title")}
          </h1>
          <p className="text-muted-foreground">{t("dashboard.subtitle")}</p>
        </div>

        {/* Scan Form */}
        <ScanForm onSubmit={handleScan} isLoading={scanMutation.isPending} />

        {/* Loading States */}
        {isLoadingCached && devices.length === 0 && (
          <div className="flex items-center justify-center p-8">
            <div className="flex items-center space-x-2 text-muted-foreground">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
              <span className="text-sm">
                {t("dashboard.loadingCached", "Loading cached results...")}
              </span>
            </div>
          </div>
        )}

        {/* Error Display */}
        {(scanMutation.error || cacheError) && (
          <div className="p-4 border border-destructive/50 bg-destructive/10 rounded-lg">
            <p className="text-sm text-destructive">
              {scanMutation.error
                ? handleApiError(scanMutation.error)
                : "Failed to load cached scan results"}
            </p>
          </div>
        )}

        {/* Device Table */}
        {devices.length > 0 && (
          <DeviceTable devices={devices} onBulkAction={handleBulkAction} />
        )}

        {/* Empty State */}
        {!isLoadingCached &&
          !scanMutation.isPending &&
          devices.length === 0 &&
          !scanMutation.error &&
          !cacheError && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">
                {t(
                  "dashboard.noDevices",
                  "No devices found. Start by scanning for devices.",
                )}
              </p>
            </div>
          )}
      </div>

      {/* Sticky Footer */}
      <Footer className="mt-8" />

      {/* Bulk Actions Dialog */}
      <BulkActionsDialog
        open={bulkActionsOpen}
        onOpenChange={setBulkActionsOpen}
        selectedDevices={selectedDevices}
        onComplete={handleBulkActionComplete}
      />
    </div>
  );
}
