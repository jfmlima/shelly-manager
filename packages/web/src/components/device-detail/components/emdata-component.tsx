import { BarChart3 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { BaseComponentCard } from "./base-component-card";
import type { EMDataComponent as EMDataComponentType } from "@/types/api";

interface EMDataComponentProps {
  component: EMDataComponentType;
  deviceIp: string;
}

function formatEnergy(wh: number | undefined): string {
  if (wh == null) return "--";
  if (wh >= 1000) return `${(wh / 1000).toFixed(2)} kWh`;
  return `${wh.toFixed(1)} Wh`;
}

export function EMDataComponent({ component, deviceIp }: EMDataComponentProps) {
  const { t } = useTranslation();
  const tk = (key: string) => t(`deviceDetail.components.emdata.${key}`);
  const { status } = component;

  return (
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-amber-500"
      icon={<BarChart3 className="h-4 w-4" />}
      title={`${tk("title")} ${component.id}`}
      description={tk("description")}
    >
      <div className="space-y-3 text-sm">
        {/* Totals */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-medium">{tk("totalEnergy")}</span>
            <span className="font-medium">
              {formatEnergy(status.total_act)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-medium">{tk("totalReturnedEnergy")}</span>
            <span className="font-medium">
              {formatEnergy(status.total_act_ret)}
            </span>
          </div>
        </div>

        {/* Per-phase breakdown */}
        <div className="border-t pt-3 space-y-2">
          {[
            {
              label: tk("phaseA"),
              consumed: status.a_total_act_energy,
              returned: status.a_total_act_ret_energy,
            },
            {
              label: tk("phaseB"),
              consumed: status.b_total_act_energy,
              returned: status.b_total_act_ret_energy,
            },
            {
              label: tk("phaseC"),
              consumed: status.c_total_act_energy,
              returned: status.c_total_act_ret_energy,
            },
          ].map((phase) => (
            <div
              key={phase.label}
              className="flex items-center justify-between"
            >
              <span className="text-muted-foreground">{phase.label}</span>
              <span className="font-medium">
                {formatEnergy(phase.consumed)}
                {phase.returned != null && phase.returned > 0 && (
                  <span className="text-muted-foreground ml-2">
                    / {formatEnergy(phase.returned)}
                  </span>
                )}
              </span>
            </div>
          ))}
        </div>
      </div>
    </BaseComponentCard>
  );
}
