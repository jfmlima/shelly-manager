import { Cable } from "lucide-react";

import { ComponentActions } from "../component-actions";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
    <Card className="border-l-4 border-l-slate-500 h-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center space-x-2">
            <Cable className="h-4 w-4" />
            <span>Ethernet</span>
          </div>
          <Badge variant={isConnected ? "default" : "destructive"}>
            {isConnected ? tUpper("connected") : tUpper("disconnected")}
          </Badge>
        </CardTitle>
        <CardDescription>Wired network connectivity status</CardDescription>
      </CardHeader>
      <CardContent className="pt-0 flex-1 flex flex-col gap-6">
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

        {/* Component Actions */}
        <div className="mt-auto pt-4 border-t">
          <ComponentActions component={component} deviceIp={deviceIp} />
        </div>
      </CardContent>
    </Card>
  );
}
