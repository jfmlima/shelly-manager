import { useTranslation } from "react-i18next";

import {
  SwitchComponent,
  InputComponent,
  CoverComponent,
  SystemComponent,
  CloudComponent,
  ZigbeeComponent,
  GenericComponent,
} from "./components";

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
  onRefresh?: () => void;
}

export function DeviceComponents({
  deviceStatus,
  isLoading,
  onRefresh,
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
    const deviceIp = deviceStatus?.ip || "";

    if (isSwitchComponent(component)) {
      return (
        <SwitchComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
          onRefresh={onRefresh}
        />
      );
    }

    if (isInputComponent(component)) {
      return (
        <InputComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
          onRefresh={onRefresh}
        />
      );
    }

    if (isCoverComponent(component)) {
      return (
        <CoverComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
          onRefresh={onRefresh}
        />
      );
    }

    if (isSystemComponent(component)) {
      return (
        <SystemComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
          onRefresh={onRefresh}
        />
      );
    }

    if (isCloudComponent(component)) {
      return (
        <CloudComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
          onRefresh={onRefresh}
        />
      );
    }

    if (isZigbeeComponent(component)) {
      return (
        <ZigbeeComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
          onRefresh={onRefresh}
        />
      );
    }

    // Generic component fallback
    return (
      <GenericComponent
        key={component.key}
        component={component}
        deviceIp={deviceIp}
        onRefresh={onRefresh}
      />
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
