import { Home, AlertTriangle } from "lucide-react";

import { BaseComponentCard } from "./base-component-card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { BluetoothHomeComponent as BluetoothHomeComponentType } from "@/types/api";
import { useTranslation } from "react-i18next";

interface BluetoothHomeComponentProps {
  component: BluetoothHomeComponentType;
  deviceIp: string;
}

export function BluetoothHomeComponent({
  component,
  deviceIp,
}: BluetoothHomeComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.bluetoothHome.${key}`).toUpperCase();

  const hasErrors =
    component.status.errors && component.status.errors.length > 0;

  return (
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-rose-500"
      icon={<Home className="h-4 w-4" />}
      title="Bluetooth Home"
      description="Bluetooth Home integration status"
      badge={{
        label: component.config.enable
          ? hasErrors
            ? tUpper("error")
            : tUpper("enabled")
          : tUpper("disabled"),
        variant: component.config.enable
          ? hasErrors
            ? "destructive"
            : "default"
          : "secondary",
      }}
    >
      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span>Enabled</span>
          <span className="font-medium">
            {component.config.enable ? "Yes" : "No"}
          </span>
        </div>
      </div>

      {hasErrors && (
        <div className="mt-4">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-1">
                {component.status.errors!.map((error, index) => (
                  <div key={index} className="text-sm">
                    {error}
                  </div>
                ))}
              </div>
            </AlertDescription>
          </Alert>
        </div>
      )}
    </BaseComponentCard>
  );
}
