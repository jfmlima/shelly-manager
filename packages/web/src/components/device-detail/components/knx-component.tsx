import { Building2 } from "lucide-react";

import { ComponentActions } from "../component-actions";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { KnxComponent as KnxComponentType } from "@/types/api";
import { useTranslation } from "react-i18next";

interface KnxComponentProps {
  component: KnxComponentType;
  deviceIp: string;
}

export function KnxComponent({ component, deviceIp }: KnxComponentProps) {
  const { t } = useTranslation();
  const tUpper = (key: string) =>
    t(`deviceDetail.components.knx.${key}`).toUpperCase();

  return (
    <Card className="border-l-4 border-l-amber-500 h-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center space-x-2">
            <Building2 className="h-4 w-4" />
            <span>KNX</span>
          </div>
          <Badge variant={component.config.enable ? "default" : "secondary"}>
            {component.config.enable ? tUpper("enabled") : tUpper("disabled")}
          </Badge>
        </CardTitle>
        <CardDescription>KNX building automation protocol</CardDescription>
      </CardHeader>
      <CardContent className="pt-0 flex-1 flex flex-col gap-6">
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span>Enabled</span>
            <span className="font-medium">
              {component.config.enable ? "Yes" : "No"}
            </span>
          </div>
          {component.config.ia && (
            <div className="flex items-center justify-between">
              <span>Individual Address</span>
              <span className="font-medium font-mono">
                {component.config.ia}
              </span>
            </div>
          )}
          {component.config.routing?.addr && (
            <div className="flex items-center justify-between">
              <span>Routing Address</span>
              <span className="font-medium font-mono">
                {component.config.routing.addr}
              </span>
            </div>
          )}
        </div>

        {/* Component Actions */}
        <div className="mt-auto pt-4 border-t">
          <ComponentActions component={component} deviceIp={deviceIp} />
        </div>
      </CardContent>
    </Card>
  );
}
