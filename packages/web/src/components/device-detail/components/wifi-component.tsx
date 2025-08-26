import { Wifi } from "lucide-react";

import { ComponentActions } from "../component-actions";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { WifiComponent as WifiComponentType } from "@/types/api";
import { useTranslation } from "react-i18next";

interface WifiComponentProps {
  component: WifiComponentType;
  deviceIp: string;
}

export function WifiComponent({ component, deviceIp }: WifiComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.wifi.${key}`).toUpperCase();

  const isConnected = component.status.status === "got ip";
  const signalStrength = component.status.rssi;

  const getSignalQuality = (rssi: number) => {
    if (rssi >= -50) return { quality: "excellent", color: "bg-green-500" };
    if (rssi >= -60) return { quality: "good", color: "bg-green-400" };
    if (rssi >= -70) return { quality: "fair", color: "bg-yellow-500" };
    return { quality: "poor", color: "bg-red-500" };
  };

  const signal = getSignalQuality(signalStrength);

  return (
    <Card className="border-l-4 border-l-emerald-500">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center space-x-2">
            <Wifi className="h-4 w-4" />
            <span>Wi-Fi</span>
          </div>
          <Badge variant={isConnected ? "default" : "destructive"}>
            {isConnected ? tUpper("connected") : tUpper("disconnected")}
          </Badge>
        </CardTitle>
        <CardDescription>Wireless network connectivity status</CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2 text-sm">
          {component.status.ssid && (
            <div className="flex items-center justify-between">
              <span>Network (SSID)</span>
              <span className="font-medium">{component.status.ssid}</span>
            </div>
          )}
          {component.status.sta_ip && (
            <div className="flex items-center justify-between">
              <span>IP Address</span>
              <span className="font-medium font-mono">
                {component.status.sta_ip}
              </span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span>Signal Strength</span>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${signal.color}`}></div>
              <span className="font-medium">{signalStrength} dBm</span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span>Status</span>
            <span className="font-medium capitalize">
              {component.status.status.replace("_", " ")}
            </span>
          </div>
          {component.status.bssid && (
            <div className="flex items-center justify-between">
              <span>BSSID</span>
              <span className="font-medium font-mono text-xs">
                {component.status.bssid}
              </span>
            </div>
          )}
          {component.status.sta_ip6 && component.status.sta_ip6.length > 0 && (
            <div className="space-y-1">
              <span className="text-xs text-muted-foreground">
                IPv6 Addresses
              </span>
              {component.status.sta_ip6.slice(0, 2).map((ip6, index) => (
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
        <div className="mt-4 pt-4 border-t">
          <ComponentActions component={component} deviceIp={deviceIp} />
        </div>
      </CardContent>
    </Card>
  );
}
