import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import {
  Download,
  Power,
  RefreshCw,
  AlertTriangle,
  AlertCircle,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { deviceApi, handleApiError } from "@/lib/api";
import type { DeviceStatus, UpdateSource } from "@/types/api";

interface DeviceActionsProps {
  ip: string;
  deviceStatus: DeviceStatus | null;
  onRefresh: () => void;
  isRefreshing?: boolean;
}

export function DeviceActions({
  ip,
  deviceStatus,
  onRefresh,
  isRefreshing = false,
}: DeviceActionsProps) {
  const { t } = useTranslation();
  const [updateChannel, setUpdateChannel] = useState<"stable" | "beta">(
    "stable",
  );
  const [updateSource, setUpdateSource] = useState<UpdateSource>("internet");
  const [rebootDialogOpen, setRebootDialogOpen] = useState(false);
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
  const [factoryResetDialogOpen, setFactoryResetDialogOpen] = useState(false);

  const updateMutation = useMutation({
    mutationFn: ({
      channel,
      source,
    }: {
      channel: "stable" | "beta";
      source: UpdateSource;
    }) =>
      deviceApi.updateDevice(
        ip,
        source === "local" ? "stable" : channel,
        source,
      ),
    onSuccess: (result) => {
      if (result.success) {
        toast.success(
          result.message || t("deviceDetail.messages.firmwareUpdateStarted"),
        );
        setUpdateDialogOpen(false);
      } else {
        toast.error(result.error || t("deviceDetail.messages.updateFailed"));
      }
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  const rebootMutation = useMutation({
    mutationFn: () => deviceApi.rebootDevice(ip),
    onSuccess: (result) => {
      if (result.success) {
        toast.success(
          result.message || t("deviceDetail.messages.deviceRebootInitiated"),
        );
        setRebootDialogOpen(false);
      } else {
        toast.error(result.error || t("deviceDetail.messages.rebootFailed"));
      }
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  const factoryResetMutation = useMutation({
    mutationFn: () => deviceApi.factoryResetDevice(ip),
    onSuccess: (result) => {
      if (result.success) {
        toast.success(
          result.message || t("deviceDetail.messages.factoryResetInitiated"),
        );
        setFactoryResetDialogOpen(false);
      } else {
        toast.error(
          result.error || t("deviceDetail.messages.factoryResetFailed"),
        );
      }
    },
    onError: (error) => {
      toast.error(handleApiError(error));
    },
  });

  const hasUpdates = deviceStatus?.summary.has_updates || false;
  const availableUpdates = deviceStatus?.firmware.available_updates || {};

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <span>{t("deviceDetail.actions.title", "Device Actions")}</span>
        </CardTitle>
        <CardDescription>
          {t("deviceDetail.actions.description")}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Refresh Status */}
          <Button
            variant="outline"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-2"
          >
            <RefreshCw
              className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`}
            />
            <span>{t("deviceDetail.actions.fetchStatus")}</span>
          </Button>

          {/* Update Firmware */}
          <Dialog open={updateDialogOpen} onOpenChange={setUpdateDialogOpen}>
            <DialogTrigger asChild>
              <Button
                variant={hasUpdates ? "default" : "outline"}
                className="flex items-center space-x-2"
              >
                <Download className="h-4 w-4" />
                <span>{t("deviceDetail.actions.update")}</span>
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="flex items-center space-x-2">
                  <Download className="h-5 w-5" />
                  <span>{t("deviceDetail.dialogs.updateFirmware.title")}</span>
                </DialogTitle>
                <DialogDescription>
                  {t("deviceDetail.dialogs.updateFirmware.description")}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-5">
                <div className="space-y-3">
                  <label className="block text-sm font-medium">
                    {t("deviceDetail.dialogs.updateFirmware.updateSource")}
                  </label>
                  <Select
                    value={updateSource}
                    onValueChange={(value: UpdateSource) =>
                      setUpdateSource(value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="internet">
                        {t(
                          "deviceDetail.dialogs.updateFirmware.sourceInternet",
                        )}
                      </SelectItem>
                      <SelectItem value="local">
                        {t("deviceDetail.dialogs.updateFirmware.sourceLocal")}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <ol className="text-xs text-muted-foreground space-y-1 pt-2">
                    {(updateSource === "local"
                      ? ["localStep1", "localStep2", "localStep3"]
                      : ["internetStep1", "internetStep2"]
                    ).map((step, index) => (
                      <li key={step} className="flex gap-2">
                        <span className="text-muted-foreground/60">
                          {index + 1}.
                        </span>
                        <span>
                          {t(`deviceDetail.dialogs.updateFirmware.${step}`)}
                        </span>
                      </li>
                    ))}
                  </ol>
                </div>

                {updateSource === "internet" && (
                  <div className="space-y-3">
                    <label className="block text-sm font-medium">
                      {t("deviceDetail.dialogs.updateFirmware.updateChannel")}
                    </label>
                    <Select
                      value={updateChannel}
                      onValueChange={(value: "stable" | "beta") =>
                        setUpdateChannel(value)
                      }
                    >
                      <SelectTrigger>
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

                {updateSource === "internet" &&
                  availableUpdates[updateChannel] && (
                    <div className="p-3 bg-muted rounded-lg space-y-2">
                      <div className="text-sm font-medium">
                        {availableUpdates[updateChannel].name ||
                          t(
                            "deviceDetail.dialogs.updateFirmware.firmwareUpdate",
                          )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {t("deviceDetail.dialogs.updateFirmware.version")}:{" "}
                        {availableUpdates[updateChannel].version}
                      </div>
                      {availableUpdates[updateChannel].desc && (
                        <div className="text-xs text-muted-foreground">
                          {availableUpdates[updateChannel].desc}
                        </div>
                      )}
                    </div>
                  )}

                {updateSource === "internet" &&
                  !availableUpdates[updateChannel] && (
                    <div className="p-3 bg-muted rounded-lg text-sm text-muted-foreground">
                      {t(
                        "deviceDetail.dialogs.updateFirmware.noReleaseOnChannel",
                      )}
                    </div>
                  )}
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setUpdateDialogOpen(false)}
                >
                  {t("common.cancel")}
                </Button>
                <Button
                  onClick={() =>
                    updateMutation.mutate({
                      channel: updateChannel,
                      source: updateSource,
                    })
                  }
                  disabled={
                    updateMutation.isPending ||
                    (updateSource === "internet" &&
                      !availableUpdates[updateChannel])
                  }
                >
                  {updateMutation.isPending
                    ? t("deviceDetail.dialogs.updateFirmware.startingUpdate")
                    : t("deviceDetail.dialogs.updateFirmware.startUpdate")}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* Reboot Device */}
          <Dialog open={rebootDialogOpen} onOpenChange={setRebootDialogOpen}>
            <DialogTrigger asChild>
              <Button
                variant="destructive"
                className="flex items-center space-x-2"
              >
                <Power className="h-4 w-4" />
                <span>{t("deviceDetail.actions.reboot")}</span>
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="flex items-center space-x-2">
                  <AlertTriangle className="h-5 w-5 text-orange-600" />
                  <span>{t("deviceDetail.dialogs.rebootDevice.title")}</span>
                </DialogTitle>
                <DialogDescription>
                  {t("confirmations.rebootDevice")}
                </DialogDescription>
              </DialogHeader>

              <div className="p-4 bg-orange-50 dark:bg-orange-950/20 rounded-lg">
                <div className="flex items-center space-x-2 text-orange-800 dark:text-orange-200">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm">
                    {t("deviceDetail.dialogs.rebootDevice.warning")}
                  </span>
                </div>
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setRebootDialogOpen(false)}
                >
                  {t("common.cancel")}
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => rebootMutation.mutate()}
                  disabled={rebootMutation.isPending}
                >
                  {rebootMutation.isPending
                    ? t("deviceDetail.dialogs.rebootDevice.rebooting")
                    : t("deviceDetail.dialogs.rebootDevice.rebootDevice")}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* Factory Reset Device */}
          <Dialog
            open={factoryResetDialogOpen}
            onOpenChange={setFactoryResetDialogOpen}
          >
            <DialogTrigger asChild>
              <Button
                variant="destructive"
                className="flex items-center space-x-2"
              >
                <AlertCircle className="h-4 w-4" />
                <span>{t("deviceDetail.actions.factoryReset")}</span>
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="flex items-center space-x-2">
                  <AlertCircle className="h-5 w-5 text-red-600" />
                  <span>{t("deviceDetail.dialogs.factoryReset.title")}</span>
                </DialogTitle>
                <DialogDescription>
                  {t("confirmations.factoryReset")}
                </DialogDescription>
              </DialogHeader>

              <div className="p-4 bg-red-50 dark:bg-red-950/20 rounded-lg">
                <div className="flex items-center space-x-2 text-red-800 dark:text-red-200">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm">
                    {t("deviceDetail.dialogs.factoryReset.warning")}
                  </span>
                </div>
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setFactoryResetDialogOpen(false)}
                >
                  {t("common.cancel")}
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => factoryResetMutation.mutate()}
                  disabled={factoryResetMutation.isPending}
                >
                  {factoryResetMutation.isPending
                    ? t("deviceDetail.dialogs.factoryReset.resetting")
                    : t("deviceDetail.dialogs.factoryReset.factoryReset")}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardContent>
    </Card>
  );
}
