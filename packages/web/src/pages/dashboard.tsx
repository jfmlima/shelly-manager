import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { ScanForm, type ScanFormData } from "@/components/dashboard/scan-form";
import { DeviceTable } from "@/components/dashboard/device-table";
import { BulkActionsDialog } from "@/components/dashboard/bulk-actions-dialog";
import { Footer } from "@/components/ui/footer";
import { deviceApi, handleApiError } from "@/lib/api";
import type { Device } from "@/types/api";

export function Dashboard() {
  const { t } = useTranslation();
  const [selectedDevices, setSelectedDevices] = useState<Device[]>([]);
  const [bulkActionsOpen, setBulkActionsOpen] = useState(false);
  const [devices, setDevices] = useState<Device[]>([]);
  const queryClient = useQueryClient();

  const scanMutation = useMutation({
    mutationFn: (params: ScanFormData) => deviceApi.scanDevices(params),
    onSuccess: (data) => {
      setDevices(data);
      toast.success(
        t("dashboard.messages.scanSuccess", { count: data.length }),
      );
      // Update the query cache
      queryClient.setQueryData(["devices", "scan"], data);
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  const handleScan = (formData: ScanFormData) => {
    scanMutation.mutate(formData);
  };

  const handleBulkAction = (devices: Device[]) => {
    setSelectedDevices(devices);
    setBulkActionsOpen(true);
  };

  const handleBulkActionComplete = () => {
    // Optionally refetch devices after bulk actions
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

        {/* Error Display */}
        {scanMutation.error && (
          <div className="p-4 border border-destructive/50 bg-destructive/10 rounded-lg">
            <p className="text-sm text-destructive">
              {handleApiError(scanMutation.error)}
            </p>
          </div>
        )}

        {/* Device Table */}
        {devices.length > 0 && (
          <DeviceTable devices={devices} onBulkAction={handleBulkAction} />
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
