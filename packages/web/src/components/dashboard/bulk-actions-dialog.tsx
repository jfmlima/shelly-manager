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
  | "export"
  | "config";

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

  const resetDialog = () => {
    setSelectedAction(null);
    setProgress(null);
    setShowDetails(false);
    setConfirmFactoryReset(false);
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

  const executeAction = async () => {
    if (!selectedAction) return;

    setProgress({
      total: selectedDevices.length,
      completed: 0,
      failed: 0,
      results: [],
      isRunning: true,
    });

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
      case "export":
        return <Upload className="h-4 w-4" />;
      case "config":
        return <Upload className="h-4 w-4" />;
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
      id: "export" as BulkActionType,
      title: t("bulkActions.exportConfigurations"),
      description: t("bulkActions.descriptions.exportConfigurations"),
      icon: <Upload className="h-6 w-6" />,
    },
    {
      id: "config" as BulkActionType,
      title: t("bulkActions.applyConfiguration"),
      description: t("bulkActions.descriptions.applyConfiguration"),
      icon: <Upload className="h-6 w-6" />,
    },
  ];

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
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
              {actionCards.map((action) => (
                <Card
                  key={action.id}
                  className={`cursor-pointer hover:shadow-md transition-shadow ${
                    action.id === "factory_reset"
                      ? "border-destructive/20 hover:border-destructive/40"
                      : ""
                  }`}
                  onClick={() => setSelectedAction(action.id)}
                >
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-3">
                      {action.icon}
                      <span>{action.title}</span>
                    </CardTitle>
                    <CardDescription>{action.description}</CardDescription>
                  </CardHeader>
                </Card>
              ))}
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

                <div className="flex space-x-2">
                  <Button
                    onClick={executeAction}
                    disabled={
                      selectedAction === "factory_reset" && !confirmFactoryReset
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
