import { useTranslation } from "react-i18next";
import { Bluetooth } from "lucide-react";

import { ComponentActions } from "../component-actions";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { BleComponent } from "@/types/api";

interface BleComponentProps {
  component: BleComponent;
  deviceIp: string;
}

export function BleComponent({ component, deviceIp }: BleComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.ble.${key}`).toUpperCase();

  const isEnabled = component.config.enable;
  const rpcEnabled = component.config.rpc?.enable;

  return (
    <Card className="border-l-4 border-l-indigo-500">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center space-x-2">
            <Bluetooth className="h-4 w-4" />
            <span>Bluetooth</span>
          </div>
          <Badge variant={isEnabled ? "default" : "secondary"}>
            {isEnabled ? tUpper("enabled") : tUpper("disabled")}
          </Badge>
        </CardTitle>
        <CardDescription>
          {t("deviceDetail.components.ble.description")}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span>{t("deviceDetail.components.ble.enabled")}</span>
            <span className="font-medium">
              {isEnabled ? t("common.yes") : t("common.no")}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>{t("deviceDetail.components.ble.rpcEnabled")}</span>
            <span className="font-medium">
              {rpcEnabled ? t("common.yes") : t("common.no")}
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
