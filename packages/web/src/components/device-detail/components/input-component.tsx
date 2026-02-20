import { Activity } from "lucide-react";

import { BaseComponentCard } from "./base-component-card";
import type { InputComponent as InputComponentType } from "@/types/api";

interface InputComponentProps {
  component: InputComponentType;
  deviceIp: string;
}

export function InputComponent({ component, deviceIp }: InputComponentProps) {
  return (
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-green-500"
      icon={<Activity className="h-4 w-4" />}
      title={`Input ${component.id}`}
      description={component.config.name || `Input ${component.id}`}
      badge={{
        label: component.status.state ? "ACTIVE" : "INACTIVE",
        variant: component.status.state ? "default" : "outline",
      }}
    >
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
    </BaseComponentCard>
  );
}
