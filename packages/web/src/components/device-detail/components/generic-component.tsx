import { ComponentActions } from "../component-actions";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Component } from "@/types/api";

interface GenericComponentProps {
  component: Component;
  deviceIp: string;
}

export function GenericComponent({
  component,
  deviceIp,
}: GenericComponentProps) {
  return (
    <Card className="border-l-4 border-l-gray-300 h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">
          {component.type} {component.id !== null ? component.id : ""}
        </CardTitle>
        <CardDescription>Component type: {component.type}</CardDescription>
      </CardHeader>
      <CardContent className="pt-0 flex-1 flex flex-col gap-6">
        <div className="text-sm text-muted-foreground">
          Key: {component.key}
        </div>

        {/* Component Actions */}
        <div className="mt-auto pt-4 border-t">
          <ComponentActions component={component} deviceIp={deviceIp} />
        </div>
      </CardContent>
    </Card>
  );
}
