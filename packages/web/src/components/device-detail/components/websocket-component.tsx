import { Zap } from "lucide-react";

import { BaseComponentCard } from "./base-component-card";
import type { WebSocketComponent as WebSocketComponentType } from "@/types/api";
import { useTranslation } from "react-i18next";

interface WebSocketComponentProps {
  component: WebSocketComponentType;
  deviceIp: string;
}

export function WebSocketComponent({
  component,
  deviceIp,
}: WebSocketComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.websocket.${key}`).toUpperCase();

  return (
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-teal-500"
      icon={<Zap className="h-4 w-4" />}
      title="WebSocket"
      description="WebSocket connection status"
      badge={{
        label: component.status.connected
          ? tUpper("connected")
          : tUpper("disconnected"),
        variant: component.status.connected ? "default" : "destructive",
      }}
    >
      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span>Connection Status</span>
          <span className="font-medium">
            {component.status.connected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </div>
    </BaseComponentCard>
  );
}
