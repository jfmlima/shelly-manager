import { Building2 } from "lucide-react";

import { BaseComponentCard } from "./base-component-card";
import type { KnxComponent as KnxComponentType } from "@/types/api";
import { useTranslation } from "react-i18next";

interface KnxComponentProps {
  component: KnxComponentType;
  deviceIp: string;
}

export function KnxComponent({ component, deviceIp }: KnxComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.knx.${key}`).toUpperCase();

  return (
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-amber-500"
      icon={<Building2 className="h-4 w-4" />}
      title="KNX"
      description="KNX building automation protocol"
      badge={{
        label: component.config.enable ? tUpper("enabled") : tUpper("disabled"),
        variant: component.config.enable ? "default" : "secondary",
      }}
    >
      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span>Enabled</span>
          <span className="font-medium">
            {component.config.enable ? "Yes" : "No"}
          </span>
        </div>
        {component.config.ia && (
          <div className="flex items-center justify-between">
            <span>Individual Address</span>
            <span className="font-medium font-mono">{component.config.ia}</span>
          </div>
        )}
        {component.config.routing?.addr && (
          <div className="flex items-center justify-between">
            <span>Routing Address</span>
            <span className="font-medium font-mono">
              {component.config.routing.addr}
            </span>
          </div>
        )}
      </div>
    </BaseComponentCard>
  );
}
