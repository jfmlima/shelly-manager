import { Home, AlertTriangle } from "lucide-react";

import { ComponentActions } from "../component-actions";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
    <Card className="border-l-4 border-l-rose-500 h-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center space-x-2">
            <Home className="h-4 w-4" />
            <span>Bluetooth Home</span>
          </div>
          <Badge
            variant={
              component.config.enable
                ? hasErrors
                  ? "destructive"
                  : "default"
                : "secondary"
            }
          >
            {component.config.enable
              ? hasErrors
                ? tUpper("error")
                : tUpper("enabled")
              : tUpper("disabled")}
          </Badge>
        </CardTitle>
        <CardDescription>Bluetooth Home integration status</CardDescription>
      </CardHeader>
      <CardContent className="pt-0 flex-1 flex flex-col gap-6">
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span>Enabled</span>
            <span className="font-medium">
              {component.config.enable ? "Yes" : "No"}
            </span>
          </div>
        </div>

        {/* Errors */}
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

        {/* Component Actions */}
        <div className="mt-auto pt-4 border-t">
          <ComponentActions component={component} deviceIp={deviceIp} />
        </div>
      </CardContent>
    </Card>
  );
}
