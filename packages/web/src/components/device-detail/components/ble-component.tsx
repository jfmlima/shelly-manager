import { useTranslation } from "react-i18next";
import { Bluetooth } from "lucide-react";

import { BaseComponentCard } from "./base-component-card";
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
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-indigo-500"
      icon={<Bluetooth className="h-4 w-4" />}
      title="Bluetooth"
      description={t("deviceDetail.components.ble.description")}
      badge={{
        label: isEnabled ? tUpper("enabled") : tUpper("disabled"),
        variant: isEnabled ? "default" : "secondary",
      }}
    >
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
    </BaseComponentCard>
  );
}
