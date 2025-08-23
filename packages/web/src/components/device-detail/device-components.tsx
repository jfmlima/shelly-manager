import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronUp } from "lucide-react";

import {
  SwitchComponent,
  InputComponent,
  CoverComponent,
  SystemComponent,
  CloudComponent,
  ZigbeeComponent,
  BleComponent,
  GenericComponent,
} from "./components";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
import {
  isSwitchComponent,
  isInputComponent,
  isCoverComponent,
  isSystemComponent,
  isCloudComponent,
  isZigbeeComponent,
  isBleComponent,
} from "@/types/api";
import type { DeviceStatus, Component } from "@/types/api";

interface DeviceComponentsProps {
  deviceStatus: DeviceStatus | null;
  isLoading?: boolean;
  onRefresh?: () => void;
}

const PRIORITY_COMPONENT_TYPES = [
  "cloud",
  "cover",
  "switch",
  "sys",
  "zigbee",
  "ble",
];

const TYPE_ORDER = ["switch", "cover", "cloud", "sys", "zigbee", "ble"];

function sortComponentsByType(components: Component[]): Component[] {
  return [...components].sort((a, b) => {
    const aIndex = TYPE_ORDER.indexOf(a.type);
    const bIndex = TYPE_ORDER.indexOf(b.type);

    if (aIndex !== -1 && bIndex !== -1) {
      return aIndex - bIndex;
    }

    if (aIndex !== -1) return -1;
    if (bIndex !== -1) return 1;

    return a.type.localeCompare(b.type);
  });
}

export function DeviceComponents({
  deviceStatus,
  isLoading,
}: DeviceComponentsProps) {
  const { t } = useTranslation();
  const [showAllComponents, setShowAllComponents] = useState(false);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="animate-pulse space-y-2">
            <div className="h-5 bg-muted rounded w-1/4"></div>
            <div className="h-4 bg-muted rounded w-1/2"></div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-20 bg-muted rounded"></div>
            <div className="h-20 bg-muted rounded"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!deviceStatus?.components) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("deviceDetail.status.components")}</CardTitle>
          <CardDescription>
            {t("deviceDetail.components.noComponentData")}
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const renderComponent = (component: Component) => {
    const deviceIp = deviceStatus?.ip || "";

    if (isSwitchComponent(component)) {
      return (
        <SwitchComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isInputComponent(component)) {
      return (
        <InputComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isCoverComponent(component)) {
      return (
        <CoverComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isSystemComponent(component)) {
      return (
        <SystemComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isCloudComponent(component)) {
      return (
        <CloudComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isZigbeeComponent(component)) {
      return (
        <ZigbeeComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isBleComponent(component)) {
      return (
        <BleComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    return (
      <GenericComponent
        key={component.key}
        component={component}
        deviceIp={deviceIp}
      />
    );
  };

  const priorityComponentsUnsorted = deviceStatus.components.filter(
    (component) => PRIORITY_COMPONENT_TYPES.includes(component.type),
  );
  const additionalComponentsUnsorted = deviceStatus.components.filter(
    (component) => !PRIORITY_COMPONENT_TYPES.includes(component.type),
  );

  const priorityComponents = sortComponentsByType(priorityComponentsUnsorted);
  const additionalComponents = sortComponentsByType(
    additionalComponentsUnsorted,
  );

  const hasAdditionalComponents = additionalComponents.length > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("deviceDetail.status.components")}</CardTitle>
        <CardDescription>
          {t("deviceDetail.components.componentsDescription", {
            count: deviceStatus.total_components,
          })}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Always visible priority components */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {priorityComponents.map(renderComponent)}
          </div>

          {/* Collapsible additional components */}
          {hasAdditionalComponents && (
            <Collapsible
              open={showAllComponents}
              onOpenChange={setShowAllComponents}
            >
              <CollapsibleContent>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-4">
                  {additionalComponents.map(renderComponent)}
                </div>
              </CollapsibleContent>

              <div className="flex justify-center pt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowAllComponents(!showAllComponents)}
                  className="text-sm"
                >
                  {showAllComponents ? (
                    <>
                      <ChevronUp className="mr-2 h-4 w-4" />
                      {t("deviceDetail.components.showLess")}
                    </>
                  ) : (
                    <>
                      <ChevronDown className="mr-2 h-4 w-4" />
                      {t("deviceDetail.components.showMore", {
                        count: additionalComponents.length,
                      })}
                    </>
                  )}
                </Button>
              </div>
            </Collapsible>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
