import { useTranslation } from "react-i18next";
import { Wifi } from "lucide-react";

import { BaseComponentCard } from "./base-component-card";
import type { ZigbeeComponent as ZigbeeComponentType } from "@/types/api";

interface ZigbeeComponentProps {
  component: ZigbeeComponentType;
  deviceIp: string;
}

export function ZigbeeComponent({ component, deviceIp }: ZigbeeComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.zigbee.${key}`).toUpperCase();

  const getStatusVariant = (networkState: string) => {
    switch (networkState.toLowerCase()) {
      case "joined":
        return "default" as const;
      case "joining":
        return "secondary" as const;
      default:
        return "destructive" as const;
    }
  };

  const getStatusLabel = (networkState: string) => {
    switch (networkState.toLowerCase()) {
      case "joined":
        return tUpper("joined");
      case "joining":
        return tUpper("joining");
      default:
        return tUpper("disconnected");
    }
  };

  return (
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-orange-500"
      icon={<Wifi className="h-4 w-4" />}
      title="Zigbee"
      description={t("deviceDetail.components.zigbee.description")}
      badge={{
        label: getStatusLabel(component.status.network_state),
        variant: getStatusVariant(component.status.network_state),
      }}
    >
      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span>{t("deviceDetail.components.zigbee.networkState")}</span>
          <span className="font-medium">
            {component.status.network_state}
          </span>
        </div>
      </div>
    </BaseComponentCard>
  );
}
