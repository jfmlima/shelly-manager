import { Cloud } from "lucide-react";

import { ComponentActions } from "../component-actions";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { CloudComponent as CloudComponentType } from "@/types/api";
import { useTranslation } from "react-i18next";

interface CloudComponentProps {
  component: CloudComponentType;
  deviceIp: string;
}

export function CloudComponent({ component, deviceIp }: CloudComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.cloud.${key}`).toUpperCase();

  return (
    <Card className="border-l-4 border-l-cyan-500 h-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center space-x-2">
            <Cloud className="h-4 w-4" />
            <span>Cloud</span>
          </div>
          <Badge
            variant={component.status.connected ? "default" : "destructive"}
          >
            {component.status.connected
              ? tUpper("connected")
              : tUpper("disconnected")}
          </Badge>
        </CardTitle>
        <CardDescription>Shelly Cloud connectivity status</CardDescription>
      </CardHeader>
      <CardContent className="pt-0 flex-1 flex flex-col gap-6">
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
        </div>

        {/* Component Actions */}
        <div className="mt-auto pt-4 border-t">
          <ComponentActions component={component} deviceIp={deviceIp} />
        </div>
      </CardContent>
    </Card>
  );
}
