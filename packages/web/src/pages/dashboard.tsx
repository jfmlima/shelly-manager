import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { ScanForm } from "@/components/dashboard/scan-form";
import { DeviceTable } from "@/components/dashboard/device-table";
import { BulkActionsDialog } from "@/components/dashboard/bulk-actions-dialog";
import { deviceApi, handleApiError } from "@/lib/api";
import type { Device } from "@/types/api";

export function Dashboard() {
  const { t } = useTranslation();
  const [selectedDevices, setSelectedDevices] = useState<Device[]>([]);
  const [bulkActionsOpen, setBulkActionsOpen] = useState(false);

  const {
    data: devices = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["devices", "scan"],
    queryFn: () => deviceApi.scanDevices({ use_predefined: true }),
    enabled: false,
  });

  const handleScan = async () => {
    try {
      await refetch();
      toast.success(
        t("dashboard.messages.scanSuccess", { count: devices.length }),
      );
    } catch (error) {
      toast.error(handleApiError(error));
    }
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
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {t("dashboard.title")}
        </h1>
        <p className="text-muted-foreground">{t("dashboard.subtitle")}</p>
      </div>

      {/* Scan Form */}
      <ScanForm onSubmit={handleScan} isLoading={isLoading} />

      {/* Error Display */}
      {error && (
        <div className="p-4 border border-destructive/50 bg-destructive/10 rounded-lg">
          <p className="text-sm text-destructive">{handleApiError(error)}</p>
        </div>
      )}

      {/* Device Table */}
      {devices.length > 0 && (
        <DeviceTable devices={devices} onBulkAction={handleBulkAction} />
      )}

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
