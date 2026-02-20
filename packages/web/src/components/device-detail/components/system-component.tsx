import { useTranslation } from "react-i18next";
import { Settings } from "lucide-react";

import { ComponentActions } from "../component-actions";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { SystemComponent as SystemComponentType } from "@/types/api";

interface SystemComponentProps {
  component: SystemComponentType;
  deviceIp: string;
}

export function SystemComponent({ component, deviceIp }: SystemComponentProps) {
  const { t } = useTranslation();

  return (
    <Card className="border-l-4 border-l-gray-500 h-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center space-x-2 text-base">
          <Settings className="h-4 w-4" />
          <span>System</span>
        </CardTitle>
        <CardDescription>
          {t("deviceDetail.components.system.description")}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0 flex-1 flex flex-col gap-6">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span>{t("deviceDetail.components.system.ramFree")}</span>
              <span className="font-medium">
                {Math.round(component.status.ram_free / 1024)}KB
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>{t("deviceDetail.components.system.ramTotal")}</span>
              <span className="font-medium">
                {Math.round(component.status.ram_size / 1024)}KB
              </span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span>{t("deviceDetail.components.system.restartRequired")}</span>
              <Badge
                variant={
                  component.status.restart_required ? "destructive" : "outline"
                }
              >
                {component.status.restart_required
                  ? t("deviceDetail.components.input.yes")
                  : t("deviceDetail.components.input.no")}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span>{t("deviceDetail.components.system.timezone")}</span>
              <span className="font-medium text-xs">
                {component.config.location?.tz ||
                  t("deviceDetail.deviceInfo.unknown")}
              </span>
            </div>
          </div>
        </div>

        {/* Component Actions */}
        <div className="mt-auto pt-4 border-t">
          <ComponentActions component={component} deviceIp={deviceIp} />
        </div>
      </CardContent>
    </Card>
  );
}
