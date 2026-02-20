import { Power, Zap, Thermometer } from "lucide-react";

import { BaseComponentCard } from "./base-component-card";
import type { SwitchComponent as SwitchComponentType } from "@/types/api";
import { useTranslation } from "react-i18next";

interface SwitchComponentProps {
  component: SwitchComponentType;
  deviceIp: string;
}

export function SwitchComponent({ component, deviceIp }: SwitchComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.switch.${key}`).toUpperCase();

  return (
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-blue-500"
      icon={<Power className="h-4 w-4" />}
      title={`Switch ${component.id}`}
      description={component.config.name || `Switch relay ${component.id}`}
      badge={{
        label: component.status.output ? tUpper("on") : tUpper("off"),
        variant: component.status.output ? "default" : "outline",
      }}
    >
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
    </BaseComponentCard>
  );
}
