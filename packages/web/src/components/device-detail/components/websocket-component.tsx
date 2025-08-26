import { Zap } from "lucide-react";

import { ComponentActions } from "../component-actions";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
    <Card className="border-l-4 border-l-teal-500">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center space-x-2">
            <Zap className="h-4 w-4" />
            <span>WebSocket</span>
          </div>
          <Badge
            variant={component.status.connected ? "default" : "destructive"}
          >
            {component.status.connected
              ? tUpper("connected")
              : tUpper("disconnected")}
          </Badge>
        </CardTitle>
        <CardDescription>WebSocket connection status</CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span>Connection Status</span>
            <span className="font-medium">
              {component.status.connected ? "Connected" : "Disconnected"}
            </span>
          </div>
        </div>

        {/* Component Actions */}
        <div className="mt-4 pt-4 border-t">
          <ComponentActions component={component} deviceIp={deviceIp} />
        </div>
      </CardContent>
    </Card>
  );
}
