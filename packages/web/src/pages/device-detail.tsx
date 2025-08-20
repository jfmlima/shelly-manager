import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { DeviceHeader } from "@/components/device-detail/device-header";
import { DeviceActions } from "@/components/device-detail/device-actions";
import { DeviceComponents } from "@/components/device-detail/device-components";
import { deviceApi, handleApiError } from "@/lib/api";

export function DeviceDetail() {
  const { t } = useTranslation();
  const { ip } = useParams<{ ip: string }>();

  const {
    data: deviceStatus,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["device", "status", ip],
    queryFn: () => deviceApi.getDeviceStatus(ip!),
    enabled: !!ip,
  });

  if (!ip) {
    return (
      <div className="space-y-4">
        <div className="text-center py-8">
          <h1 className="text-2xl font-bold text-destructive">
            {t("deviceDetail.errors.invalidDeviceIp")}
          </h1>
          <p className="text-muted-foreground">
            {t("deviceDetail.errors.noDeviceIpProvided")}
          </p>
          <Button asChild className="mt-4">
            <Link to="/">{t("deviceDetail.errors.returnToDashboard")}</Link>
          </Button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="relative">
          <div className="absolute left-0 top-0">
            <Button variant="outline" size="sm" asChild>
              <Link to="/">
                <ArrowLeft className="h-4 w-4 mr-2" />
                {t("deviceDetail.backToDashboard")}
              </Link>
            </Button>
          </div>
        </div>

        <div className="text-center py-8">
          <h1 className="text-2xl font-bold text-destructive">
            {t("deviceDetail.errors.errorLoadingDevice")}
          </h1>
          <p className="text-muted-foreground mt-2">{handleApiError(error)}</p>
          <div className="mt-4 space-x-2">
            <Button onClick={() => refetch()}>{t("common.retry")}</Button>
            <Button variant="outline" asChild>
              <Link to="/">{t("deviceDetail.errors.returnToDashboard")}</Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with navigation */}
      <div className="relative">
        <div className="absolute left-0 top-0">
          <Button variant="outline" size="sm" asChild>
            <Link to="/">
              <ArrowLeft className="h-4 w-4 mr-2" />
              {t("deviceDetail.backToDashboard")}
            </Link>
          </Button>
        </div>
        <div className="text-center">
          <h1 className="text-2xl font-bold">
            {deviceStatus?.summary.device_name ||
              t("deviceDetail.deviceInfo.unnamedDevice")}
          </h1>
          <p className="text-muted-foreground">
            {t("deviceDetail.subtitle", {
              name:
                deviceStatus?.summary.device_name ||
                t("deviceDetail.deviceInfo.unnamedDevice"),
              ip,
            })}
          </p>
        </div>
      </div>

      {/* Device Information Header */}
      <DeviceHeader deviceStatus={deviceStatus || null} isLoading={isLoading} />

      {/* Device Actions */}
      <DeviceActions
        ip={ip}
        deviceStatus={deviceStatus || null}
        onRefresh={() => refetch()}
        isRefreshing={isLoading}
      />

      {/* Device Components */}
      <DeviceComponents
        deviceStatus={deviceStatus || null}
        isLoading={isLoading}
        onRefresh={() => refetch()}
      />
    </div>
  );
}
