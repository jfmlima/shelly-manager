import { useTranslation } from "react-i18next";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DevicePreviewProps } from "../types";

export function DevicePreview({ selectedDevices }: DevicePreviewProps) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">
          {t("bulkActions.selectedDevices")}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {selectedDevices.map((device) => (
            <Badge key={device.ip} variant="outline">
              {device.device_name || device.ip}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
