import { BaseComponentCard } from "./base-component-card";
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
    <BaseComponentCard
      component={component}
      deviceIp={deviceIp}
      borderColor="border-l-gray-300"
      title={`${component.type} ${component.id !== null ? component.id : ""}`}
      description={`Component type: ${component.type}`}
    >
      <div className="text-sm text-muted-foreground">Key: {component.key}</div>
    </BaseComponentCard>
  );
}
