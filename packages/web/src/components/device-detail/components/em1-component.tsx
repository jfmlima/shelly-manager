import { Gauge, Zap } from "lucide-react";
import { useTranslation } from "react-i18next";

import { BaseComponentCard } from "./base-component-card";
import type { EM1Component as EM1ComponentType } from "@/types/api";

interface EM1ComponentProps {
  component: EM1ComponentType;
  deviceIp: string;
}

function formatValue(
  value: number | undefined,
  decimals: number,
  unit: string,
) {
  if (value == null) return `--${unit}`;
  return `${value.toFixed(decimals)}${unit}`;
}

export function EM1Component({ component, deviceIp }: EM1ComponentProps) {
  const { t } = useTranslation();
  const tk = (key: string) => t(`deviceDetail.components.em1.${key}`);
  const { status, config } = component;

  const power = status.act_power;
  const badgeLabel = power != null ? `${power.toFixed(1)} W` : "-- W";

  return (
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-yellow-500"
      icon={<Gauge className="h-4 w-4" />}
      title={config.name || `${tk("title")} ${component.id}`}
      description={tk("description")}
      badge={{ label: badgeLabel, variant: "default" }}
    >
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="flex items-center space-x-1">
              <Zap className="h-3 w-3 text-muted-foreground" />
              <span>{tk("activePower")}</span>
            </span>
            <span className="font-medium">{formatValue(power, 1, "W")}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>{tk("voltage")}</span>
            <span className="font-medium">
              {formatValue(status.voltage, 1, "V")}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>{tk("current")}</span>
            <span className="font-medium">
              {formatValue(status.current, 3, "A")}
            </span>
          </div>
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span>{tk("apparentPower")}</span>
            <span className="font-medium">
              {formatValue(status.aprt_power, 1, "VA")}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>{tk("powerFactor")}</span>
            <span className="font-medium">
              {status.pf != null ? status.pf.toFixed(2) : "--"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>{tk("frequency")}</span>
            <span className="font-medium">
              {formatValue(status.freq, 1, "Hz")}
            </span>
          </div>
          {config.ct_type && (
            <div className="flex items-center justify-between">
              <span>{tk("ctType")}</span>
              <span className="font-medium">{config.ct_type}</span>
            </div>
          )}
          {config.reverse && (
            <div className="flex items-center justify-between">
              <span>{tk("reverse")}</span>
              <span className="font-medium">{t("common.yes")}</span>
            </div>
          )}
        </div>
      </div>
    </BaseComponentCard>
  );
}
