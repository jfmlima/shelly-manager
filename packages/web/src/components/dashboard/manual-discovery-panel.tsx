import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  List,
  Network,
} from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  isValidIPv4,
  cidrToRange,
  getCommonCIDR,
  isValidRangeOrCIDR,
  parseManualIPs,
} from "@/lib/ip-utils";

export type ManualMode = "ips" | "range_cidr";

interface ManualDiscoveryPanelProps {
  manualMode: ManualMode;
  manualIPs: string;
  rangeCIDR: string;
  onManualModeChange: (mode: ManualMode) => void;
  onManualIPsChange: (value: string) => void;
  onRangeCIDRChange: (value: string) => void;
}

export function ManualDiscoveryPanel({
  manualMode,
  manualIPs,
  rangeCIDR,
  onManualModeChange,
  onManualIPsChange,
  onRangeCIDRChange,
}: ManualDiscoveryPanelProps) {
  const { t } = useTranslation();
  const [ipCount, setIPCount] = useState<number | null>(null);

  // Calculate IP count when inputs change
  useEffect(() => {
    if (manualMode === "ips") {
      const ips = parseManualIPs(manualIPs);
      setIPCount(ips.length > 0 ? ips.length : null);
    } else if (manualMode === "range_cidr") {
      const trimmed = rangeCIDR.trim();
      if (trimmed.includes("/")) {
        const range = cidrToRange(trimmed);
        setIPCount(range?.count || null);
      } else if (trimmed.includes("-")) {
        const parts = trimmed.split("-");
        if (parts.length === 2) {
          const [start, end] = parts;
          if (isValidIPv4(start)) {
            let fullEnd = end;
            if (!end.includes(".")) {
              const startParts = start.split(".");
              fullEnd = [...startParts.slice(0, 3), end].join(".");
            }
            if (isValidIPv4(fullEnd)) {
              const startInt = ipToInt(start);
              const endInt = ipToInt(fullEnd);
              setIPCount(endInt >= startInt ? endInt - startInt + 1 : null);
              return;
            }
          }
        }
        setIPCount(null);
      } else if (isValidIPv4(trimmed)) {
        setIPCount(1);
      } else {
        setIPCount(null);
      }
    }
  }, [manualMode, manualIPs, rangeCIDR]);

  // ipToInt helper for local calculation
  function ipToInt(ip: string): number {
    const parts = ip.split(".").map(Number);
    return (
      ((parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]) >>> 0
    );
  }

  // Quick fill handlers
  const handleQuickFill = (size: "24" | "16") => {
    const baseIP = "192.168.1.0";
    const cidrNotation = getCommonCIDR(baseIP, size);
    onRangeCIDRChange(cidrNotation);
    onManualModeChange("range_cidr");
  };

  // Validation states
  const manualIPsValid = manualIPs
    ? parseManualIPs(manualIPs).length > 0
    : null;
  const rangeCIDRValid = rangeCIDR ? isValidRangeOrCIDR(rangeCIDR) : null;

  return (
    <div className="space-y-4">
      <Tabs
        value={manualMode}
        onValueChange={(v) => onManualModeChange(v as ManualMode)}
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="ips" className="flex items-center gap-2">
            <List className="h-4 w-4" />
            <span>{t("dashboard.scanForm.custom.manualIps")}</span>
          </TabsTrigger>
          <TabsTrigger value="range_cidr" className="flex items-center gap-2">
            <Network className="h-4 w-4" />
            <span>{t("dashboard.scanForm.custom.rangeCidr")}</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="ips" className="pt-4 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="manual-ips" className="text-sm font-semibold">
              {t("dashboard.scanForm.custom.ipsInputLabel")}
            </Label>
            <div className="relative">
              <Textarea
                id="manual-ips"
                placeholder={"192.168.1.100\n192.168.1.101, 192.168.1.102"}
                value={manualIPs}
                onChange={(e) => onManualIPsChange(e.target.value)}
                className={`min-h-[100px] font-mono text-sm ${
                  manualIPsValid === false
                    ? "border-red-500 focus-visible:ring-red-500"
                    : manualIPsValid === true
                      ? "border-green-500 focus-visible:ring-green-500"
                      : ""
                }`}
              />
              {manualIPsValid !== null && (
                <div className="absolute right-3 top-3">
                  {manualIPsValid ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-500" />
                  )}
                </div>
              )}
            </div>
            <p className="text-[10px] text-muted-foreground italic">
              {t("dashboard.scanForm.custom.ipsInputHint")}
            </p>
          </div>
        </TabsContent>

        <TabsContent value="range_cidr" className="pt-4 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="range-cidr" className="text-sm font-semibold">
              {t("dashboard.scanForm.custom.rangeCidrLabel")}
            </Label>
            <div className="relative">
              <Input
                id="range-cidr"
                placeholder="192.168.1.1-50 or 192.168.1.0/24"
                value={rangeCIDR}
                onChange={(e) => onRangeCIDRChange(e.target.value)}
                className={
                  rangeCIDRValid === false
                    ? "border-red-500 focus-visible:ring-red-500"
                    : rangeCIDRValid === true
                      ? "border-green-500 focus-visible:ring-green-500"
                      : ""
                }
              />
              {rangeCIDRValid !== null && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  {rangeCIDRValid ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-500" />
                  )}
                </div>
              )}
            </div>

            {rangeCIDRValid && rangeCIDR.includes("/") && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1.5 px-1">
                <ChevronRight className="h-3 w-3" />
                {(() => {
                  const range = cidrToRange(rangeCIDR);
                  return range
                    ? t("dashboard.scanForm.custom.cidrPreview", {
                        start: range.start,
                        end: range.end,
                      })
                    : null;
                })()}
              </div>
            )}
          </div>

          <div className="space-y-2.5">
            <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              {t("dashboard.scanForm.custom.quickFill")}
            </Label>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleQuickFill("24")}
                className="h-8 text-xs bg-muted/50"
              >
                192.168.1.0/24
                <Badge
                  variant="secondary"
                  className="ml-2 px-1.5 h-4.5 text-[10px]"
                >
                  256 IPs
                </Badge>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => handleQuickFill("16")}
                className="h-8 text-xs bg-muted/50"
              >
                192.168.0.0/16
                <Badge
                  variant="secondary"
                  className="ml-2 px-1.5 h-4.5 text-[10px]"
                >
                  65,536 IPs
                </Badge>
              </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {ipCount !== null && (
        <div className="flex items-center gap-2 pt-2 border-t mt-4">
          <div className="text-sm text-muted-foreground font-medium">
            {t("dashboard.scanForm.custom.willScan")}
          </div>
          <Badge
            variant={ipCount > 512 ? "destructive" : "secondary"}
            className="px-2"
          >
            {ipCount.toLocaleString()} {t("dashboard.scanForm.custom.ips")}
          </Badge>
          {ipCount > 512 && (
            <span className="text-xs font-semibold text-destructive animate-pulse">
              {t("dashboard.scanForm.custom.largeRangeWarning")}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
