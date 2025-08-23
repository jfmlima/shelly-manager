import { ComponentActions } from "../component-actions";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { CloudComponent as CloudComponentType } from "@/types/api";

interface CloudComponentProps {
  component: CloudComponentType;
  deviceIp: string;
}

export function CloudComponent({ component, deviceIp }: CloudComponentProps) {
  return (
    <Card className="border-l-4 border-l-cyan-500">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center space-x-2">
            <div className="h-4 w-4">☁️</div>
            <span>Cloud</span>
          </div>
          <Badge
            variant={component.status.connected ? "default" : "destructive"}
          >
            {component.status.connected ? "CONNECTED" : "DISCONNECTED"}
          </Badge>
        </CardTitle>
        <CardDescription>Shelly Cloud connectivity status</CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span>Enabled</span>
            <span className="font-medium">
              {component.config.enable ? "Yes" : "No"}
            </span>
          </div>
          {component.config.server && (
            <div className="flex items-center justify-between">
              <span>Server</span>
              <span className="font-medium text-xs">
                {component.config.server}
              </span>
            </div>
          )}
        </div>

        {/* Component Actions */}
        <div className="mt-4 pt-4 border-t">
          <ComponentActions component={component} deviceIp={deviceIp} />
        </div>
      </CardContent>
    </Card>
  );
}
