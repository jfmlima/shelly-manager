import { Gauge, Zap } from "lucide-react";
import { useTranslation } from "react-i18next";

import { BaseComponentCard } from "./base-component-card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { EMComponent as EMComponentType } from "@/types/api";

interface EMComponentProps {
  component: EMComponentType;
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

function PhaseTab({
  voltage,
  current,
  activePower,
  apparentPower,
  pf,
  freq,
}: {
  voltage?: number;
  current?: number;
  activePower?: number;
  apparentPower?: number;
  pf?: number;
  freq?: number;
}) {
  const { t } = useTranslation();
  const tk = (key: string) => t(`deviceDetail.components.em.${key}`);

  return (
    <div className="space-y-2 text-sm">
      <div className="flex items-center justify-between">
        <span className="flex items-center space-x-1">
          <Zap className="h-3 w-3 text-muted-foreground" />
          <span>{tk("activePower")}</span>
        </span>
        <span className="font-medium">{formatValue(activePower, 1, "W")}</span>
      </div>
      <div className="flex items-center justify-between">
        <span>{tk("voltage")}</span>
        <span className="font-medium">{formatValue(voltage, 1, "V")}</span>
      </div>
      <div className="flex items-center justify-between">
        <span>{tk("current")}</span>
        <span className="font-medium">{formatValue(current, 3, "A")}</span>
      </div>
      <div className="flex items-center justify-between">
        <span>{tk("apparentPower")}</span>
        <span className="font-medium">
          {formatValue(apparentPower, 1, "VA")}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span>{tk("powerFactor")}</span>
        <span className="font-medium">{pf != null ? pf.toFixed(2) : "--"}</span>
      </div>
      <div className="flex items-center justify-between">
        <span>{tk("frequency")}</span>
        <span className="font-medium">{formatValue(freq, 1, "Hz")}</span>
      </div>
    </div>
  );
}

export function EMComponent({ component, deviceIp }: EMComponentProps) {
  const { t } = useTranslation();
  const tk = (key: string) => t(`deviceDetail.components.em.${key}`);
  const { status, config } = component;

  const totalPower = status.total_act_power;
  const badgeLabel = totalPower != null ? `${totalPower.toFixed(1)} W` : "-- W";

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
      <div className="space-y-3">
        {/* Summary row */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <div className="flex items-center justify-between">
            <span className="flex items-center space-x-1">
              <Zap className="h-3 w-3 text-muted-foreground" />
              <span>{tk("totalPower")}</span>
            </span>
            <span className="font-medium">
              {formatValue(totalPower, 1, "W")}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>{tk("totalCurrent")}</span>
            <span className="font-medium">
              {formatValue(status.total_current, 3, "A")}
            </span>
          </div>
          {status.n_current != null && (
            <div className="flex items-center justify-between">
              <span>{tk("neutralCurrent")}</span>
              <span className="font-medium">
                {formatValue(status.n_current, 3, "A")}
              </span>
            </div>
          )}
          {config.ct_type && (
            <div className="flex items-center justify-between">
              <span>{tk("ctType")}</span>
              <span className="font-medium">{config.ct_type}</span>
            </div>
          )}
        </div>

        {/* Phase tabs */}
        <Tabs defaultValue="a">
          <TabsList className="w-full">
            <TabsTrigger value="a">{tk("phaseA")}</TabsTrigger>
            <TabsTrigger value="b">{tk("phaseB")}</TabsTrigger>
            <TabsTrigger value="c">{tk("phaseC")}</TabsTrigger>
          </TabsList>
          <TabsContent value="a">
            <PhaseTab
              voltage={status.a_voltage}
              current={status.a_current}
              activePower={status.a_act_power}
              apparentPower={status.a_aprt_power}
              pf={status.a_pf}
              freq={status.a_freq}
            />
          </TabsContent>
          <TabsContent value="b">
            <PhaseTab
              voltage={status.b_voltage}
              current={status.b_current}
              activePower={status.b_act_power}
              apparentPower={status.b_aprt_power}
              pf={status.b_pf}
              freq={status.b_freq}
            />
          </TabsContent>
          <TabsContent value="c">
            <PhaseTab
              voltage={status.c_voltage}
              current={status.c_current}
              activePower={status.c_act_power}
              apparentPower={status.c_aprt_power}
              pf={status.c_pf}
              freq={status.c_freq}
            />
          </TabsContent>
        </Tabs>
      </div>
    </BaseComponentCard>
  );
}
