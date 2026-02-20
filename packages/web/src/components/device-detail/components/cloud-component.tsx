import { Cloud } from "lucide-react";

import { BaseComponentCard } from "./base-component-card";
import type { CloudComponent as CloudComponentType } from "@/types/api";
import { useTranslation } from "react-i18next";

interface CloudComponentProps {
  component: CloudComponentType;
  deviceIp: string;
}

export function CloudComponent({ component, deviceIp }: CloudComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.cloud.${key}`).toUpperCase();

  return (
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-cyan-500"
      icon={<Cloud className="h-4 w-4" />}
      title="Cloud"
      description="Shelly Cloud connectivity status"
      badge={{
        label: component.status.connected
          ? tUpper("connected")
          : tUpper("disconnected"),
        variant: component.status.connected ? "default" : "destructive",
      }}
    >
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
    </BaseComponentCard>
  );
}
