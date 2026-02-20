import { Cable } from "lucide-react";

import { BaseComponentCard } from "./base-component-card";
import type { EthernetComponent as EthernetComponentType } from "@/types/api";
import { useTranslation } from "react-i18next";

interface EthernetComponentProps {
  component: EthernetComponentType;
  deviceIp: string;
}

export function EthernetComponent({
  component,
  deviceIp,
}: EthernetComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.ethernet.${key}`).toUpperCase();

  const isConnected = !!component.status.ip;

  return (
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-slate-500"
      icon={<Cable className="h-4 w-4" />}
      title="Ethernet"
      description="Wired network connectivity status"
      badge={{
        label: isConnected ? tUpper("connected") : tUpper("disconnected"),
        variant: isConnected ? "default" : "destructive",
      }}
    >
      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span>Enabled</span>
          <span className="font-medium">
            {component.config.enable ? "Yes" : "No"}
          </span>
        </div>
        {component.status.ip && (
          <div className="flex items-center justify-between">
            <span>IP Address</span>
            <span className="font-medium font-mono">
              {component.status.ip}
            </span>
          </div>
        )}
        <div className="flex items-center justify-between">
          <span>IPv4 Mode</span>
          <span className="font-medium">
            {component.config.ipv4mode || "DHCP"}
          </span>
        </div>
        {component.config.gw && (
          <div className="flex items-center justify-between">
            <span>Gateway</span>
            <span className="font-medium font-mono">
              {component.config.gw}
            </span>
          </div>
        )}
        {component.config.nameserver && (
          <div className="flex items-center justify-between">
            <span>DNS</span>
            <span className="font-medium font-mono">
              {component.config.nameserver}
            </span>
          </div>
        )}
        {component.status.ip6 && component.status.ip6.length > 0 && (
          <div className="space-y-1">
            <span className="text-xs text-muted-foreground">
              IPv6 Addresses
            </span>
            {component.status.ip6.slice(0, 2).map((ip6, index) => (
              <div
                key={index}
                className="text-xs font-mono bg-muted p-1 rounded"
              >
                {ip6}
              </div>
            ))}
          </div>
        )}
      </div>
    </BaseComponentCard>
  );
}
