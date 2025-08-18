import { useTranslation } from "react-i18next";
import {
  Power,
  Thermometer,
  Zap,
  Activity,
  Settings,
  Wifi,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  isSwitchComponent,
  isInputComponent,
  isCoverComponent,
  isSystemComponent,
  isCloudComponent,
  isZigbeeComponent,
} from "@/types/api";
import type { DeviceStatus, Component } from "@/types/api";

interface DeviceComponentsProps {
  deviceStatus: DeviceStatus | null;
  isLoading?: boolean;
}

export function DeviceComponents({
  deviceStatus,
  isLoading,
}: DeviceComponentsProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="animate-pulse space-y-2">
            <div className="h-5 bg-muted rounded w-1/4"></div>
            <div className="h-4 bg-muted rounded w-1/2"></div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-20 bg-muted rounded"></div>
            <div className="h-20 bg-muted rounded"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!deviceStatus?.components) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("deviceDetail.status.components")}</CardTitle>
          <CardDescription>
            {t("deviceDetail.components.noComponentData")}
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const renderComponent = (component: Component) => {
    if (isSwitchComponent(component)) {
      return (
        <Card key={component.key} className="border-l-4 border-l-blue-500">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-base">
              <div className="flex items-center space-x-2">
                <Power className="h-4 w-4" />
                <span>Switch {component.id}</span>
              </div>
              <Badge variant={component.status.output ? "default" : "outline"}>
                {component.status.output ? "ON" : "OFF"}
              </Badge>
            </CardTitle>
            <CardDescription>
              {component.config.name || `Switch relay ${component.id}`}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-1">
                    <Zap className="h-3 w-3 text-muted-foreground" />
                    <span>Power</span>
                  </span>
                  <span className="font-medium">
                    {component.status.apower?.toFixed(1) || "0"}W
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Voltage</span>
                  <span className="font-medium">
                    {component.status.voltage?.toFixed(1) || "0"}V
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Current</span>
                  <span className="font-medium">
                    {(component.status.current * 1000)?.toFixed(0) || "0"}mA
                  </span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span>Frequency</span>
                  <span className="font-medium">
                    {component.status.freq?.toFixed(1) || "0"}Hz
                  </span>
                </div>
                {component.status.temperature && (
                  <div className="flex items-center justify-between">
                    <span className="flex items-center space-x-1">
                      <Thermometer className="h-3 w-3 text-muted-foreground" />
                      <span>Temp</span>
                    </span>
                    <span className="font-medium">
                      {component.status.temperature.tC?.toFixed(1)}°C
                    </span>
                  </div>
                )}
                {component.status.aenergy && (
                  <div className="flex items-center justify-between">
                    <span>Energy</span>
                    <span className="font-medium">
                      {component.status.aenergy.total?.toFixed(2) || "0"}Wh
                    </span>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      );
    }

    if (isInputComponent(component)) {
      return (
        <Card key={component.key} className="border-l-4 border-l-green-500">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-base">
              <div className="flex items-center space-x-2">
                <Activity className="h-4 w-4" />
                <span>Input {component.id}</span>
              </div>
              <Badge variant={component.status.state ? "default" : "outline"}>
                {component.status.state ? "ACTIVE" : "INACTIVE"}
              </Badge>
            </CardTitle>
            <CardDescription>
              {component.config.name || `Input ${component.id}`}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span>Type</span>
                  <span className="font-medium">{component.config.type}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Enabled</span>
                  <span className="font-medium">
                    {component.config.enable ? "Yes" : "No"}
                  </span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span>Inverted</span>
                  <span className="font-medium">
                    {component.config.invert ? "Yes" : "No"}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      );
    }

    if (isCoverComponent(component)) {
      return (
        <Card key={component.key} className="border-l-4 border-l-purple-500">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-base">
              <div className="flex items-center space-x-2">
                <div className="h-4 w-4">🏠</div>
                <span>Cover {component.id}</span>
              </div>
              <Badge variant="outline">{component.status.state}</Badge>
            </CardTitle>
            <CardDescription>
              {component.config.name || `Cover ${component.id}`}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span>Position</span>
                  <span className="font-medium">
                    {component.status.current_pos || 0}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Power</span>
                  <span className="font-medium">
                    {component.status.apower?.toFixed(1) || "0"}W
                  </span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span>Direction</span>
                  <span className="font-medium">
                    {component.status.last_direction}
                  </span>
                </div>
                {component.status.temperature && (
                  <div className="flex items-center justify-between">
                    <span>Temperature</span>
                    <span className="font-medium">
                      {component.status.temperature.tC?.toFixed(1)}°C
                    </span>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      );
    }

    if (isSystemComponent(component)) {
      return (
        <Card key={component.key} className="border-l-4 border-l-gray-500">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center space-x-2 text-base">
              <Settings className="h-4 w-4" />
              <span>System</span>
            </CardTitle>
            <CardDescription>
              {t("deviceDetail.components.system.description")}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span>{t("deviceDetail.components.system.ramFree")}</span>
                  <span className="font-medium">
                    {Math.round(component.status.ram_free / 1024)}KB
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>{t("deviceDetail.components.system.ramTotal")}</span>
                  <span className="font-medium">
                    {Math.round(component.status.ram_size / 1024)}KB
                  </span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span>
                    {t("deviceDetail.components.system.restartRequired")}
                  </span>
                  <Badge
                    variant={
                      component.status.restart_required
                        ? "destructive"
                        : "outline"
                    }
                  >
                    {component.status.restart_required
                      ? t("deviceDetail.components.input.yes")
                      : t("deviceDetail.components.input.no")}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span>{t("deviceDetail.components.system.timezone")}</span>
                  <span className="font-medium text-xs">
                    {component.config.location?.tz ||
                      t("deviceDetail.deviceInfo.unknown")}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      );
    }

    if (isCloudComponent(component)) {
      return (
        <Card key={component.key} className="border-l-4 border-l-cyan-500">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-base">
              <div className="flex items-center space-x-2">
                <div className="h-4 w-4">☁️</div>
                <span>Cloud</span>
              </div>
              <Badge
                variant={component.status.connected ? "default" : "destructive"}
              >
                {component.status.connected ? "CONNECTED" : "DISCONNECTED"}
              </Badge>
            </CardTitle>
            <CardDescription>Shelly Cloud connectivity status</CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span>Enabled</span>
                <span className="font-medium">
                  {component.config.enable ? "Yes" : "No"}
                </span>
              </div>
              {component.config.server && (
                <div className="flex items-center justify-between">
                  <span>Server</span>
                  <span className="font-medium text-xs">
                    {component.config.server}
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      );
    }

    if (isZigbeeComponent(component)) {
      const getStatusVariant = (networkState: string) => {
        switch (networkState.toLowerCase()) {
          case "joined":
            return "default";
          case "joining":
            return "secondary";
          default:
            return "destructive";
        }
      };

      const getStatusLabel = (networkState: string) => {
        switch (networkState.toLowerCase()) {
          case "joined":
            return t("deviceDetail.components.zigbee.joined");
          case "joining":
            return t("deviceDetail.components.zigbee.joining");
          default:
            return t("deviceDetail.components.zigbee.disconnected");
        }
      };

      return (
        <Card key={component.key} className="border-l-4 border-l-orange-500">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-base">
              <div className="flex items-center space-x-2">
                <Wifi className="h-4 w-4" />
                <span>Zigbee</span>
              </div>
              <Badge variant={getStatusVariant(component.status.network_state)}>
                {getStatusLabel(component.status.network_state)}
              </Badge>
            </CardTitle>
            <CardDescription>
              {t("deviceDetail.components.zigbee.description")}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span>{t("deviceDetail.components.zigbee.networkState")}</span>
                <span className="font-medium">
                  {component.status.network_state}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      );
    }

    // Generic component fallback
    return (
      <Card key={component.key} className="border-l-4 border-l-gray-300">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">
            {component.type} {component.id !== null ? component.id : ""}
          </CardTitle>
          <CardDescription>Component type: {component.type}</CardDescription>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="text-sm text-muted-foreground">
            Key: {component.key}
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("deviceDetail.status.components")}</CardTitle>
        <CardDescription>
          {t("deviceDetail.components.componentsDescription", {
            count: deviceStatus.total_components,
          })}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {deviceStatus.components.map(renderComponent)}
        </div>
      </CardContent>
    </Card>
  );
}
