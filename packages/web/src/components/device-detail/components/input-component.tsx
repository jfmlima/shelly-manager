import { Activity } from "lucide-react";

import { ComponentActions } from "../component-actions";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { InputComponent as InputComponentType } from "@/types/api";

interface InputComponentProps {
  component: InputComponentType;
  deviceIp: string;
}

export function InputComponent({ component, deviceIp }: InputComponentProps) {
  return (
    <Card className="border-l-4 border-l-green-500 h-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center space-x-2">
            <Activity className="h-4 w-4" />
            <span>Input {component.id}</span>
          </div>
          <Badge variant={component.status.state ? "default" : "outline"}>
            {component.status.state ? "ACTIVE" : "INACTIVE"}
          </Badge>
        </CardTitle>
        <CardDescription>
          {component.config.name || `Input ${component.id}`}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0 flex-1 flex flex-col gap-6">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span>Type</span>
              <span className="font-medium">{component.config.type}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Enabled</span>
              <span className="font-medium">
                {component.config.enable ? "Yes" : "No"}
              </span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span>Inverted</span>
              <span className="font-medium">
                {component.config.invert ? "Yes" : "No"}
              </span>
            </div>
          </div>
        </div>

        {/* Component Actions */}
        <div className="mt-auto pt-4 border-t">
          <ComponentActions component={component} deviceIp={deviceIp} />
        </div>
      </CardContent>
    </Card>
  );
}
