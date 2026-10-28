import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ChevronDown, WifiOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { Device } from "@/types/api";

interface ScanFailuresProps {
  failures: Device[];
}

export function ScanFailures({ failures }: ScanFailuresProps) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const ordered = [...failures].sort((a, b) => {
    if (a.status === b.status) return 0;
    return a.status === "error" ? -1 : 1;
  });

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className="rounded-lg border bg-card text-card-foreground"
    >
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          className="w-full justify-between px-4 py-3 h-auto font-normal"
        >
          <span className="flex items-center gap-2">
            <WifiOff className="h-4 w-4 text-muted-foreground" />
            {t("dashboard.scanFailures.title", { count: failures.length })}
          </span>
          <ChevronDown
            className={`h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
          />
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="px-4 pb-4 space-y-3">
        <p className="text-sm text-muted-foreground">
          {t("dashboard.scanFailures.description")}
        </p>
        <ul className="space-y-1 text-sm font-mono">
          {ordered.map((device) => (
            <li key={device.ip} className="flex flex-wrap gap-x-2">
              <span>{device.ip}</span>
              <span className="text-muted-foreground">
                {t(`dashboard.scanFailures.${device.status}`)}:{" "}
                {device.error_message || t("dashboard.scanFailures.noReason")}
              </span>
            </li>
          ))}
        </ul>
      </CollapsibleContent>
    </Collapsible>
  );
}
