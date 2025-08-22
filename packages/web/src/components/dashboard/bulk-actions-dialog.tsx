import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation } from "@tanstack/react-query";
import {
  Power,
  Download,
  Upload,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Checkbox } from "@/components/ui/checkbox";
import { deviceApi, handleApiError } from "@/lib/api";
import type { Device, ActionResult } from "@/types/api";

interface BulkActionsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedDevices: Device[];
  onComplete?: () => void;
}

type BulkActionType =
  | "update"
  | "reboot"
  | "factory_reset"
  | "status"
  | "export_config"
  | "apply_config";

interface BulkProgress {
  total: number;
  completed: number;
  failed: number;
  results: ActionResult[];
  isRunning: boolean;
}

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
  const [progress, setProgress] = useState<BulkProgress | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [confirmFactoryReset, setConfirmFactoryReset] = useState(false);

  // Configuration-specific state
  const [selectedComponentTypes, setSelectedComponentTypes] = useState<
    string[]
  >([]);
  const [selectedComponentType, setSelectedComponentType] =
    useState<string>("");
  const [configurationJson, setConfigurationJson] = useState<string>("");
  const [configError, setConfigError] = useState<string>("");

  // Hardcoded list of component types that support GetConfig/SetConfig
  const CONFIGURABLE_COMPONENT_TYPES = [
    "switch",
    "input",
    "cover",
    "sys",
    "cloud",
    "wifi",
    "ble",
    "mqtt",
    "ws",
    "script",
    "knx",
    "modbus",
    "zigbee",
  ];

  const resetDialog = () => {
    setSelectedAction(null);
    setProgress(null);
    setShowDetails(false);
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

  const bulkUpdateMutation = useMutation({
    mutationFn: async () => {
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
    mutationFn: async () => {
      const deviceIps = selectedDevices.map((device) => device.ip);
      return deviceApi.bulkExportConfig(deviceIps, selectedComponentTypes);
    },
    onSuccess: (result) => {
      // Download the exported configuration
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
    mutationFn: async () => {
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

  // Validate JSON configuration
  const validateConfiguration = (jsonString: string): boolean => {
    if (!jsonString.trim()) {
      setConfigError(t("bulkActions.messages.noConfigurationProvided"));
      return false;
    }

    try {
      JSON.parse(jsonString);
      setConfigError("");
      return true;
    } catch {
      setConfigError(t("bulkActions.messages.invalidJsonConfig"));
      return false;
    }
  };

  const executeAction = async () => {
    if (!selectedAction) return;

    setProgress({
      total: selectedDevices.length,
      completed: 0,
      failed: 0,
      results: [],
      isRunning: true,
    });

    // Validation for config actions
    if (selectedAction === "export_config") {
      if (selectedComponentTypes.length === 0) {
        toast.error(t("bulkActions.messages.noComponentTypesSelected"));
        setProgress((prev) => (prev ? { ...prev, isRunning: false } : null));
        return;
      }
    }

    if (selectedAction === "apply_config") {
      if (!selectedComponentType) {
        toast.error(t("bulkActions.messages.noComponentTypesSelected"));
        setProgress((prev) => (prev ? { ...prev, isRunning: false } : null));
        return;
      }

      if (!validateConfiguration(configurationJson)) {
        setProgress((prev) => (prev ? { ...prev, isRunning: false } : null));
        return;
      }
    }

    switch (selectedAction) {
      case "update":
        bulkUpdateMutation.mutate();
        break;
      case "reboot":
        bulkRebootMutation.mutate();
        break;
      case "factory_reset":
        bulkFactoryResetMutation.mutate();
        break;
      case "export_config":
        bulkExportConfigMutation.mutate();
        break;
      case "apply_config":
        bulkApplyConfigMutation.mutate();
        break;
      default:
        toast.error(t("bulkActions.messages.actionNotImplemented"));
        setProgress((prev) => (prev ? { ...prev, isRunning: false } : null));
    }
  };

  const getActionIcon = (action: BulkActionType) => {
    switch (action) {
      case "update":
        return <Download className="h-4 w-4" />;
      case "reboot":
        return <Power className="h-4 w-4" />;
      case "factory_reset":
        return <AlertCircle className="h-4 w-4" />;
      case "status":
        return <RefreshCw className="h-4 w-4" />;
      case "export_config":
        return <Upload className="h-4 w-4" />;
      case "apply_config":
        return <Download className="h-4 w-4" />;
    }
  };

  const getResultIcon = (success: boolean) => {
    return success ? (
      <CheckCircle className="h-4 w-4 text-green-600" />
    ) : (
      <XCircle className="h-4 w-4 text-red-600" />
    );
  };

  const actionCards = [
    {
      id: "update" as BulkActionType,
      title: t("bulkActions.updateFirmware"),
      description: t("bulkActions.descriptions.updateFirmware"),
      icon: <Download className="h-6 w-6" />,
    },
    {
      id: "reboot" as BulkActionType,
      title: t("bulkActions.rebootDevices"),
      description: t("bulkActions.descriptions.rebootDevices"),
      icon: <Power className="h-6 w-6" />,
    },
    {
      id: "factory_reset" as BulkActionType,
      title: t("bulkActions.factoryReset"),
      description: t("bulkActions.descriptions.factoryReset"),
      icon: <AlertCircle className="h-6 w-6" />,
    },
    {
      id: "status" as BulkActionType,
      title: t("bulkActions.checkStatus"),
      description: t("bulkActions.descriptions.checkStatus"),
      icon: <RefreshCw className="h-6 w-6" />,
    },
    {
      id: "export_config" as BulkActionType,
      title: t("bulkActions.exportConfigurations"),
      description: t("bulkActions.descriptions.exportConfigurations"),
      icon: <Upload className="h-6 w-6" />,
    },
    {
      id: "apply_config" as BulkActionType,
      title: t("bulkActions.applyConfiguration"),
      description: t("bulkActions.descriptions.applyConfiguration"),
      icon: <Download className="h-6 w-6" />,
    },
  ];

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] min-w-[40vw]  overflow-y-auto">
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
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">
                {t("bulkActions.selectedDevices")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {selectedDevices.map((device) => (
                  <Badge key={device.ip} variant="outline">
                    {device.device_name || device.ip}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Action Selection */}
          {!selectedAction && !progress && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {actionCards.map((action) => {
                const isComingSoon = action.id === "status";
                return (
                  <Card
                    key={action.id}
                    className={`transition-shadow ${
                      isComingSoon
                        ? "opacity-60 cursor-not-allowed"
                        : `cursor-pointer hover:shadow-md ${
                            action.id === "factory_reset"
                              ? "border-destructive/20 hover:border-destructive/40"
                              : ""
                          }`
                    }`}
                    onClick={() =>
                      !isComingSoon && setSelectedAction(action.id)
                    }
                  >
                    <CardHeader>
                      <CardTitle className="flex items-center space-x-3">
                        {action.icon}
                        <span>{action.title}</span>
                      </CardTitle>
                      {isComingSoon && (
                        <Badge
                          variant="secondary"
                          className="text-xs w-fit mb-2 mt-2"
                        >
                          {t("common.comingSoon")}
                        </Badge>
                      )}
                      <CardDescription>
                        {isComingSoon
                          ? t("bulkActions.comingSoonDescription")
                          : action.description}
                      </CardDescription>
                    </CardHeader>
                  </Card>
                );
              })}
            </div>
          )}

          {/* Action Configuration */}
          {selectedAction && !progress && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  {getActionIcon(selectedAction)}
                  <span>
                    {actionCards.find((a) => a.id === selectedAction)?.title}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {selectedAction === "update" && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      {t("bulkActions.channel")}
                    </label>
                    <Select
                      value={updateChannel}
                      onValueChange={(value: "stable" | "beta") =>
                        setUpdateChannel(value)
                      }
                    >
                      <SelectTrigger className="w-48">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="stable">
                          {t("bulkActions.stable")}
                        </SelectItem>
                        <SelectItem value="beta">
                          {t("bulkActions.beta")}
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {selectedAction === "factory_reset" && (
                  <div className="space-y-4 p-4 bg-destructive/5 border border-destructive/20 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="h-5 w-5 text-destructive" />
                      <span className="font-medium text-destructive">
                        {t("bulkActions.warnings.factoryReset")}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {t("bulkActions.warnings.factoryResetDescription")}
                    </p>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="confirm-factory-reset"
                        checked={confirmFactoryReset}
                        onCheckedChange={(checked) =>
                          setConfirmFactoryReset(checked === true)
                        }
                      />
                      <label
                        htmlFor="confirm-factory-reset"
                        className="text-sm font-medium"
                      >
                        {t("bulkActions.confirmFactoryReset")}
                      </label>
                    </div>
                  </div>
                )}

                {/* Component Selection for Export Config */}
                {selectedAction === "export_config" && (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">
                        {t("bulkActions.componentSelection")}
                      </label>
                      <p className="text-sm text-muted-foreground">
                        {t("bulkActions.selectComponentTypes")}
                      </p>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {CONFIGURABLE_COMPONENT_TYPES.map((componentType) => (
                          <div
                            key={componentType}
                            className="flex items-center space-x-2"
                          >
                            <Checkbox
                              id={`component-${componentType}`}
                              checked={selectedComponentTypes.includes(
                                componentType,
                              )}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  setSelectedComponentTypes([
                                    ...selectedComponentTypes,
                                    componentType,
                                  ]);
                                } else {
                                  setSelectedComponentTypes(
                                    selectedComponentTypes.filter(
                                      (t) => t !== componentType,
                                    ),
                                  );
                                }
                              }}
                            />
                            <label
                              htmlFor={`component-${componentType}`}
                              className="text-sm font-medium capitalize"
                            >
                              {componentType}
                            </label>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Component Selection and Configuration for Apply Config */}
                {selectedAction === "apply_config" && (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">
                        {t("bulkActions.componentSelection")}
                      </label>
                      <p className="text-sm text-muted-foreground">
                        {t("bulkActions.selectSingleComponentType")}
                      </p>
                      <Select
                        value={selectedComponentType}
                        onValueChange={setSelectedComponentType}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select component type" />
                        </SelectTrigger>
                        <SelectContent>
                          {CONFIGURABLE_COMPONENT_TYPES.map((componentType) => (
                            <SelectItem
                              key={componentType}
                              value={componentType}
                            >
                              <span className="capitalize">
                                {componentType}
                              </span>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">
                        {t("bulkActions.configurationEditor")}
                      </label>
                      <p className="text-sm text-muted-foreground">
                        {t("bulkActions.pasteJsonConfig")}
                      </p>
                      <textarea
                        className="w-full h-32 p-3 border rounded-lg font-mono text-sm"
                        placeholder='{"example": "configuration"}'
                        value={configurationJson}
                        onChange={(e) => {
                          setConfigurationJson(e.target.value);
                          if (configError) {
                            validateConfiguration(e.target.value);
                          }
                        }}
                        onBlur={() => validateConfiguration(configurationJson)}
                      />
                      {configError && (
                        <p className="text-sm text-red-600">{configError}</p>
                      )}
                    </div>

                    {selectedComponentType && (
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <AlertCircle className="h-5 w-5 text-blue-600" />
                          <span className="font-medium text-blue-800">
                            {t("bulkActions.configurationDiff")}
                          </span>
                        </div>
                        <p className="text-sm text-blue-700 mt-2">
                          {t("bulkActions.applyToComponents", {
                            componentType: selectedComponentType,
                          })}
                        </p>
                      </div>
                    )}

                    <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <AlertCircle className="h-5 w-5 text-orange-600" />
                        <span className="font-medium text-orange-800">
                          {t("bulkActions.safetyWarning")}
                        </span>
                      </div>
                      <p className="text-sm text-orange-700 mt-2">
                        {t("bulkActions.backupResponsibility")}
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex space-x-2">
                  <Button
                    onClick={executeAction}
                    disabled={
                      (selectedAction === "factory_reset" &&
                        !confirmFactoryReset) ||
                      (selectedAction === "export_config" &&
                        selectedComponentTypes.length === 0) ||
                      (selectedAction === "apply_config" &&
                        (!selectedComponentType || !configurationJson.trim()))
                    }
                  >
                    {t("common.confirm")}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setSelectedAction(null)}
                  >
                    {t("common.cancel")}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Progress Section */}
          {progress && (
            <Card>
              <CardHeader>
                <CardTitle>{t("bulkActions.progress")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{t("bulkActions.overallProgress")}</span>
                    <span>
                      {progress.completed + progress.failed} / {progress.total}
                    </span>
                  </div>
                  <Progress
                    value={
                      ((progress.completed + progress.failed) /
                        progress.total) *
                      100
                    }
                    className="w-full"
                  />
                </div>

                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {progress.completed}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {t("bulkActions.successful")}
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-red-600">
                      {progress.failed}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {t("bulkActions.failed")}
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold">
                      {progress.total - progress.completed - progress.failed}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {t("bulkActions.pending")}
                    </div>
                  </div>
                </div>

                {progress.results.length > 0 && (
                  <Collapsible open={showDetails} onOpenChange={setShowDetails}>
                    <CollapsibleTrigger asChild>
                      <Button variant="outline" className="w-full">
                        <span>{t("bulkActions.viewDetails")}</span>
                        {showDetails ? (
                          <ChevronDown className="ml-2 h-4 w-4" />
                        ) : (
                          <ChevronRight className="ml-2 h-4 w-4" />
                        )}
                      </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="space-y-2 mt-4">
                      {progress.results.map((result) => (
                        <div
                          key={result.ip}
                          className="flex items-center justify-between p-3 border rounded-lg"
                        >
                          <div className="flex items-center space-x-3">
                            {getResultIcon(result.success)}
                            <span className="font-mono text-sm">
                              {result.ip}
                            </span>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {result.success ? result.message : result.error}
                          </div>
                        </div>
                      ))}
                    </CollapsibleContent>
                  </Collapsible>
                )}

                {!progress.isRunning && (
                  <div className="flex space-x-2">
                    <Button onClick={handleClose}>{t("common.close")}</Button>
                    <Button variant="outline" onClick={resetDialog}>
                      {t("bulkActions.startNewAction")}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
