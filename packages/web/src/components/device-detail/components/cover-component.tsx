import { PanelTopClose } from "lucide-react";

import { BaseComponentCard } from "./base-component-card";
import type { CoverComponent as CoverComponentType } from "@/types/api";

interface CoverComponentProps {
  component: CoverComponentType;
  deviceIp: string;
}

export function CoverComponent({ component, deviceIp }: CoverComponentProps) {
  return (
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-purple-500"
      icon={<PanelTopClose className="h-4 w-4" />}
      title={`Cover ${component.id}`}
      description={component.config.name || `Cover ${component.id}`}
      badge={{
        label: component.status.state?.toUpperCase() || "UNKNOWN",
        variant: "outline",
      }}
    >
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
    </BaseComponentCard>
  );
}
