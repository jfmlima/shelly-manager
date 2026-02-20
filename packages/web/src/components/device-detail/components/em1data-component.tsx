import { BarChart3 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { BaseComponentCard } from "./base-component-card";
import type { EM1DataComponent as EM1DataComponentType } from "@/types/api";

interface EM1DataComponentProps {
  component: EM1DataComponentType;
  deviceIp: string;
}

function formatEnergy(wh: number | undefined): string {
  if (wh == null) return "--";
  if (wh >= 1000) return `${(wh / 1000).toFixed(2)} kWh`;
  return `${wh.toFixed(1)} Wh`;
}

export function EM1DataComponent({
  component,
  deviceIp,
}: EM1DataComponentProps) {
  const { t } = useTranslation();
  const tk = (key: string) => t(`deviceDetail.components.em1data.${key}`);
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
      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span>{tk("totalEnergy")}</span>
          <span className="font-medium">
            {formatEnergy(status.total_act_energy)}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span>{tk("totalReturnedEnergy")}</span>
          <span className="font-medium">
            {formatEnergy(status.total_act_ret_energy)}
          </span>
        </div>
      </div>
    </BaseComponentCard>
  );
}
