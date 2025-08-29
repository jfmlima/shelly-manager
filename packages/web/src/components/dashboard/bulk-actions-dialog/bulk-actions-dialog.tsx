import { useState } from "react";
import { useTranslation } from "react-i18next";
import { AlertCircle } from "lucide-react";
import { toast } from "sonner";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { useBulkActions } from "./hooks/use-bulk-actions";
import { useBulkProgress } from "./hooks/use-bulk-progress";
import { DevicePreview } from "./components/device-preview";
import { ActionSelection } from "./components/action-selection";
import { ActionConfiguration } from "./components/action-configuration";
import { ProgressDisplay } from "./components/progress-display";

import type { BulkActionsDialogProps, BulkActionType } from "./types";

export function BulkActionsDialog({
  open,
  onOpenChange,
  selectedDevices,
  onComplete,
}: BulkActionsDialogProps) {
  const { t } = useTranslation();

  const [selectedAction, setSelectedAction] = useState<BulkActionType | null>(
    null,
  );

  const [updateChannel, setUpdateChannel] = useState<"stable" | "beta">(
    "stable",
  );
  const [confirmFactoryReset, setConfirmFactoryReset] = useState(false);
  const [selectedComponentTypes, setSelectedComponentTypes] = useState<
    string[]
  >([]);
  const [selectedComponentType, setSelectedComponentType] =
    useState<string>("");
  const [configurationJson, setConfigurationJson] = useState<string>("");
  const [configError, setConfigError] = useState<string>("");

  const {
    progress,
    setProgress,
    showDetails,
    setShowDetails,
    initializeProgress,
    resetProgress,
  } = useBulkProgress();

  const {
    bulkUpdateMutation,
    bulkRebootMutation,
    bulkFactoryResetMutation,
    bulkExportConfigMutation,
    bulkApplyConfigMutation,
  } = useBulkActions({
    selectedDevices,
    onComplete,
    setProgress,
  });

  const resetDialog = () => {
    setSelectedAction(null);
    resetProgress();
    setConfirmFactoryReset(false);
    setSelectedComponentTypes([]);
    setSelectedComponentType("");
    setConfigurationJson("");
    setConfigError("");
  };

  const handleClose = () => {
    if (!progress?.isRunning) {
      resetDialog();
      onOpenChange(false);
    }
  };

  const handleConfigurationJsonChange = (json: string) => {
    setConfigurationJson(json);
    if (configError) {
      setConfigError("");
    }
  };

  const executeAction = async () => {
    if (!selectedAction) return;

    initializeProgress(selectedDevices.length, selectedAction);

    if (selectedAction === "export_config") {
      if (selectedComponentTypes.length === 0) {
        toast.error(t("bulkActions.messages.noComponentTypesSelected"));
        resetProgress();
        return;
      }
    }

    if (selectedAction === "apply_config") {
      if (!selectedComponentType) {
        toast.error(t("bulkActions.messages.noComponentTypesSelected"));
        resetProgress();
        return;
      }

      if (!configurationJson.trim()) {
        toast.error(t("bulkActions.messages.noConfigurationProvided"));
        resetProgress();
        return;
      }
    }

    switch (selectedAction) {
      case "update":
        bulkUpdateMutation.mutate(updateChannel);
        break;
      case "reboot":
        bulkRebootMutation.mutate();
        break;
      case "factory_reset":
        bulkFactoryResetMutation.mutate();
        break;
      case "export_config":
        bulkExportConfigMutation.mutate(selectedComponentTypes);
        break;
      case "apply_config":
        bulkApplyConfigMutation.mutate({
          selectedComponentType,
          configurationJson,
        });
        break;
      default:
        toast.error(t("bulkActions.messages.actionNotImplemented"));
        resetProgress();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] min-w-[40vw] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5" />
            <span>{t("bulkActions.title")}</span>
          </DialogTitle>
          <DialogDescription>
            {t("bulkActions.description", { count: selectedDevices.length })}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Selected Devices Preview */}
          <DevicePreview selectedDevices={selectedDevices} />

          {/* Action Selection */}
          {!selectedAction && !progress && (
            <ActionSelection onActionSelect={setSelectedAction} />
          )}

          {/* Action Configuration */}
          {selectedAction && !progress && (
            <ActionConfiguration
              selectedAction={selectedAction}
              updateChannel={updateChannel}
              onUpdateChannelChange={setUpdateChannel}
              confirmFactoryReset={confirmFactoryReset}
              onConfirmFactoryResetChange={setConfirmFactoryReset}
              selectedComponentTypes={selectedComponentTypes}
              onSelectedComponentTypesChange={setSelectedComponentTypes}
              selectedComponentType={selectedComponentType}
              onSelectedComponentTypeChange={setSelectedComponentType}
              configurationJson={configurationJson}
              onConfigurationJsonChange={handleConfigurationJsonChange}
              configError={configError}
              onExecute={executeAction}
              onCancel={() => setSelectedAction(null)}
            />
          )}

          {/* Progress Section */}
          {progress && (
            <ProgressDisplay
              progress={progress}
              showDetails={showDetails}
              onShowDetailsChange={setShowDetails}
              onClose={handleClose}
              onReset={resetDialog}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
