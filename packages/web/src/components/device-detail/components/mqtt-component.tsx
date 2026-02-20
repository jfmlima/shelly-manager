import { MessageSquare } from "lucide-react";

import { BaseComponentCard } from "./base-component-card";
import type { MqttComponent as MqttComponentType } from "@/types/api";
import { useTranslation } from "react-i18next";

interface MqttComponentProps {
  component: MqttComponentType;
  deviceIp: string;
}

export function MqttComponent({ component, deviceIp }: MqttComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.mqtt.${key}`).toUpperCase();

  return (
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-violet-500"
      icon={<MessageSquare className="h-4 w-4" />}
      title="MQTT"
      description="MQTT messaging service status"
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
        {component.config.client_id && (
          <div className="flex items-center justify-between">
            <span>Client ID</span>
            <span className="font-medium text-xs">
              {component.config.client_id}
            </span>
          </div>
        )}
        {component.config.topic_prefix && (
          <div className="flex items-center justify-between">
            <span>Topic Prefix</span>
            <span className="font-medium text-xs">
              {component.config.topic_prefix}
            </span>
          </div>
        )}
        <div className="flex items-center justify-between">
          <span>RPC Enabled</span>
          <span className="font-medium">
            {component.config.enable_rpc ? "Yes" : "No"}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span>Control Enabled</span>
          <span className="font-medium">
            {component.config.enable_control ? "Yes" : "No"}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span>Status Notifications</span>
          <span className="font-medium">
            {component.config.status_ntf ? "Yes" : "No"}
          </span>
        </div>
        {component.config.use_client_cert && (
          <div className="flex items-center justify-between">
            <span>Client Certificate</span>
            <span className="font-medium">
              {component.config.use_client_cert ? "Yes" : "No"}
            </span>
          </div>
        )}
      </div>
    </BaseComponentCard>
  );
}
