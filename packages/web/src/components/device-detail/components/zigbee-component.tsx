import { useTranslation } from "react-i18next";
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
import type { ZigbeeComponent as ZigbeeComponentType } from "@/types/api";

interface ZigbeeComponentProps {
  component: ZigbeeComponentType;
  deviceIp: string;
}

export function ZigbeeComponent({ component, deviceIp }: ZigbeeComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.zigbee.${key}`).toUpperCase();

  const getStatusVariant = (networkState: string) => {
    switch (networkState.toLowerCase()) {
      case "joined":
        return "default";
      case "joining":
        return "secondary";
      default:
        return "destructive";
    }
  };

  const getStatusLabel = (networkState: string) => {
    switch (networkState.toLowerCase()) {
      case "joined":
        return tUpper("joined");
      case "joining":
        return tUpper("joining");
      default:
        return tUpper("disconnected");
    }
  };

  return (
    <Card className="border-l-4 border-l-orange-500">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center space-x-2">
            <Wifi className="h-4 w-4" />
            <span>Zigbee</span>
          </div>
          <Badge variant={getStatusVariant(component.status.network_state)}>
            {getStatusLabel(component.status.network_state)}
          </Badge>
        </CardTitle>
        <CardDescription>
          {t("deviceDetail.components.zigbee.description")}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span>{t("deviceDetail.components.zigbee.networkState")}</span>
            <span className="font-medium">
              {component.status.network_state}
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
