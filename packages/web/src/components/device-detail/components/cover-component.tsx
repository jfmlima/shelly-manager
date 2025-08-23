import { ComponentActions } from "../component-actions";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { CoverComponent as CoverComponentType } from "@/types/api";

interface CoverComponentProps {
  component: CoverComponentType;
  deviceIp: string;
}

export function CoverComponent({ component, deviceIp }: CoverComponentProps) {
  return (
    <Card className="border-l-4 border-l-purple-500">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center space-x-2">
            <div className="h-4 w-4">🏠</div>
            <span>Cover {component.id}</span>
          </div>
          <Badge variant="outline">{component.status.state}</Badge>
        </CardTitle>
        <CardDescription>
          {component.config.name || `Cover ${component.id}`}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span>Position</span>
              <span className="font-medium">
                {component.status.current_pos || 0}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Power</span>
              <span className="font-medium">
                {component.status.apower?.toFixed(1) || "0"}W
              </span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span>Direction</span>
              <span className="font-medium">
                {component.status.last_direction}
              </span>
            </div>
            {component.status.temperature && (
              <div className="flex items-center justify-between">
                <span>Temperature</span>
                <span className="font-medium">
                  {component.status.temperature.tC?.toFixed(1)}°C
                </span>
              </div>
            )}
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
