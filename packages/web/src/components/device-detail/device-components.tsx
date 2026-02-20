import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, ChevronUp } from "lucide-react";

import {
  SwitchComponent,
  InputComponent,
  CoverComponent,
  EMComponent,
  EM1Component,
  EMDataComponent,
  EM1DataComponent,
  SystemComponent,
  CloudComponent,
  ZigbeeComponent,
  BleComponent,
  EthernetComponent,
  WifiComponent,
  MqttComponent,
  BluetoothHomeComponent,
  KnxComponent,
  WebSocketComponent,
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
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
  isSwitchComponent,
  isInputComponent,
  isCoverComponent,
  isEMComponent,
  isEM1Component,
  isEMDataComponent,
  isEM1DataComponent,
  isSystemComponent,
  isCloudComponent,
  isZigbeeComponent,
  isBleComponent,
  isEthernetComponent,
  isWifiComponent,
  isMqttComponent,
  isBluetoothHomeComponent,
  isKnxComponent,
  isWebSocketComponent,
} from "@/types/api";
import type { DeviceStatus, Component } from "@/types/api";

type ComponentFilter = "all" | "active" | "inactive";

interface DeviceComponentsProps {
  deviceStatus: DeviceStatus | null;
  isLoading?: boolean;
  onRefresh?: () => void;
}

const VISIBLE_COUNT = 6;

const TYPE_ORDER = [
  "switch",
  "cover",
  "em",
  "em1",
  "emdata",
  "em1data",
  "zigbee",
  "wifi",
  "eth",
  "cloud",
  "sys",
  "mqtt",
  "ws",
  "ble",
  "bthome",
  "knx",
];

function isComponentActive(component: Component): boolean {
  switch (component.type) {
    case "cloud":
    case "mqtt":
    case "ws":
      return component.status.connected === true;
    case "wifi":
      return component.status.status === "got ip";
    case "eth":
      return component.status.ip != null;
    case "zigbee":
      return component.status.network_state === "joined";
    case "ble":
    case "knx":
    case "modbus":
      return component.config.enable === true;
    case "bthome": {
      const errors = component.status.errors;
      return !Array.isArray(errors) || errors.length === 0;
    }
    default:
      return true;
  }
}

function sortComponentsByType(components: Component[]): Component[] {
  return [...components].sort((a, b) => {
    const aIndex = TYPE_ORDER.indexOf(a.type);
    const bIndex = TYPE_ORDER.indexOf(b.type);

    if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
    if (aIndex !== -1) return -1;
    if (bIndex !== -1) return 1;

    return a.type.localeCompare(b.type);
  });
}

function filterComponents(
  components: Component[],
  filter: ComponentFilter,
): Component[] {
  if (filter === "all") return components;
  if (filter === "active") return components.filter(isComponentActive);
  return components.filter((c) => !isComponentActive(c));
}

export function DeviceComponents({
  deviceStatus,
  isLoading,
}: DeviceComponentsProps) {
  const { t } = useTranslation();
  const [showAllComponents, setShowAllComponents] = useState(false);
  const [componentFilter, setComponentFilter] =
    useState<ComponentFilter>("all");

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

    if (isEMComponent(component)) {
      return (
        <EMComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isEM1Component(component)) {
      return (
        <EM1Component
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isEMDataComponent(component)) {
      return (
        <EMDataComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isEM1DataComponent(component)) {
      return (
        <EM1DataComponent
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

    if (isEthernetComponent(component)) {
      return (
        <EthernetComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isWifiComponent(component)) {
      return (
        <WifiComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isMqttComponent(component)) {
      return (
        <MqttComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isBluetoothHomeComponent(component)) {
      return (
        <BluetoothHomeComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isKnxComponent(component)) {
      return (
        <KnxComponent
          key={component.key}
          component={component}
          deviceIp={deviceIp}
        />
      );
    }

    if (isWebSocketComponent(component)) {
      return (
        <WebSocketComponent
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

  const sorted = sortComponentsByType(
    filterComponents(deviceStatus.components, componentFilter),
  );
  const visibleComponents = sorted.slice(0, VISIBLE_COUNT);
  const collapsedComponents = sorted.slice(VISIBLE_COUNT);
  const hasCollapsed = collapsedComponents.length > 0;

  const renderComponentCard = (component: Component) => (
    <div
      key={component.key}
      className={`h-full${
        isComponentActive(component)
          ? ""
          : " opacity-50 transition-opacity hover:opacity-100"
      }`}
    >
      {renderComponent(component)}
    </div>
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle>{t("deviceDetail.status.components")}</CardTitle>
            <CardDescription>
              {t("deviceDetail.components.componentsDescription", {
                count: deviceStatus.total_components,
              })}
            </CardDescription>
          </div>
          <ToggleGroup
            type="single"
            value={componentFilter}
            onValueChange={(value) => {
              if (value) setComponentFilter(value as ComponentFilter);
            }}
            variant="outline"
            size="sm"
          >
            <ToggleGroupItem value="all">
              {t("deviceDetail.components.filterAll")}
            </ToggleGroupItem>
            <ToggleGroupItem value="active">
              {t("deviceDetail.components.filterActive")}
            </ToggleGroupItem>
            <ToggleGroupItem value="inactive">
              {t("deviceDetail.components.filterInactive")}
            </ToggleGroupItem>
          </ToggleGroup>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {visibleComponents.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {visibleComponents.map(renderComponentCard)}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              {t("deviceDetail.components.noMatchingComponents")}
            </p>
          )}

          {hasCollapsed && (
            <Collapsible
              open={showAllComponents}
              onOpenChange={setShowAllComponents}
            >
              <CollapsibleContent>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-4">
                  {collapsedComponents.map(renderComponentCard)}
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
                        count: collapsedComponents.length,
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
