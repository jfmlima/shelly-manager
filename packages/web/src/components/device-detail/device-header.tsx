import {
  Wifi,
  WifiOff,
  Power,
  Activity,
  HardDrive,
  Clock,
  Zap,
} from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { DeviceStatus } from "@/types/api";

interface DeviceHeaderProps {
  deviceStatus: DeviceStatus | null;
  isLoading?: boolean;
}

export function DeviceHeader({ deviceStatus, isLoading }: DeviceHeaderProps) {
  const { t } = useTranslation();
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="animate-pulse space-y-2">
            <div className="h-6 bg-muted rounded w-1/3"></div>
            <div className="h-4 bg-muted rounded w-1/2"></div>
          </div>
        </CardHeader>
      </Card>
    );
  }

  if (!deviceStatus) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            {t("deviceDetail.deviceInfo.deviceInformation")}
          </CardTitle>
          <CardDescription>
            {t("deviceDetail.deviceInfo.noDeviceData")}
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const { summary, ip } = deviceStatus;

  const getStatusBadge = () => {
    return (
      <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
        {t("deviceDetail.deviceInfo.online")}
      </Badge>
    );
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Device Info Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <CardTitle className="flex items-center space-x-2">
                <span>
                  {summary.device_name ||
                    t("deviceDetail.deviceInfo.unnamedDevice")}
                </span>
                {getStatusBadge()}
              </CardTitle>
              <CardDescription className="font-mono">{ip}</CardDescription>
            </div>
            <div className="text-right space-y-1">
              <div className="text-sm text-muted-foreground">
                {t("deviceDetail.status.macAddress")}
              </div>
              <div className="font-mono text-xs">
                {summary.mac_address || t("deviceDetail.deviceInfo.unknown")}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <HardDrive className="h-4 w-4 text-muted-foreground" />
                <span>{t("deviceDetail.deviceInfo.firmware")}</span>
              </div>
              <div className="font-mono text-xs pl-6">
                {summary.firmware_version ||
                  t("deviceDetail.deviceInfo.unknown")}
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span>{t("deviceDetail.status.uptime")}</span>
              </div>
              <div className="pl-6">{formatUptime(summary.uptime)}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Status Overview Card */}
      <Card>
        <CardHeader>
          <CardTitle>{t("deviceDetail.deviceInfo.overview")}</CardTitle>
          <CardDescription>
            {t("deviceDetail.deviceInfo.overviewDescription")}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="flex items-center space-x-2">
                  <Power className="h-4 w-4 text-muted-foreground" />
                  <span>{t("deviceDetail.deviceInfo.switches")}</span>
                </span>
                <Badge variant="outline">{summary.switch_count}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center space-x-2">
                  <Activity className="h-4 w-4 text-muted-foreground" />
                  <span>{t("deviceDetail.deviceInfo.inputs")}</span>
                </span>
                <Badge variant="outline">{summary.input_count}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center space-x-2">
                  <div className="h-4 w-4 text-muted-foreground">⚡</div>
                  <span>{t("deviceDetail.deviceInfo.covers")}</span>
                </span>
                <Badge variant="outline">{summary.cover_count}</Badge>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="flex items-center space-x-2">
                  <Zap className="h-4 w-4 text-muted-foreground" />
                  <span>{t("deviceDetail.deviceInfo.power")}</span>
                </span>
                <Badge variant="outline">
                  {summary.total_power.toFixed(1)}W
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center space-x-2">
                  {summary.cloud_connected ? (
                    <Wifi className="h-4 w-4 text-green-600" />
                  ) : (
                    <WifiOff className="h-4 w-4 text-red-600" />
                  )}
                  <span>{t("deviceDetail.deviceInfo.cloud")}</span>
                </span>
                <Badge
                  variant={summary.cloud_connected ? "default" : "destructive"}
                >
                  {summary.cloud_connected
                    ? t("deviceDetail.deviceInfo.connected")
                    : t("deviceDetail.deviceInfo.disconnected")}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center space-x-2">
                  <div className="h-4 w-4 text-muted-foreground">🔄</div>
                  <span>{t("deviceDetail.deviceInfo.updates")}</span>
                </span>
                <Badge variant={summary.has_updates ? "secondary" : "outline"}>
                  {summary.has_updates
                    ? t("deviceDetail.deviceInfo.available")
                    : t("deviceDetail.deviceInfo.upToDate")}
                </Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
