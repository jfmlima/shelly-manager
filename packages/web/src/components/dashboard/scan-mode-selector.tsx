import { Info, Search, Radio } from "lucide-react";
import { useTranslation } from "react-i18next";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export type ScanMode = "mdns" | "manual";

interface ScanModeSelectorProps {
  value: ScanMode;
  onValueChange: (value: ScanMode) => void;
}

export function ScanModeSelector({
  value,
  onValueChange,
}: ScanModeSelectorProps) {
  const { t } = useTranslation();

  return (
    <div className="space-y-3">
      <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
        {t("dashboard.scanForm.scanMode")}
      </label>
      <ToggleGroup
        type="single"
        value={value}
        onValueChange={(val) => val && onValueChange(val as ScanMode)}
        className="grid grid-cols-1 md:grid-cols-2 gap-3"
      >
        <ToggleGroupItem
          value="manual"
          className="flex flex-col items-start h-auto p-4 space-y-1 text-left border-2 border-transparent data-[state=on]:border-primary data-[state=on]:bg-primary/5 hover:bg-muted"
        >
          <div className="flex items-center gap-2 font-semibold">
            <Search className="h-4 w-4" />
            <span>{t("dashboard.scanForm.modes.manual.title")}</span>
          </div>
          <div className="text-xs text-muted-foreground">
            {t("dashboard.scanForm.modes.manual.description")}
          </div>
        </ToggleGroupItem>

        <ToggleGroupItem
          value="mdns"
          className="flex flex-col items-start h-auto p-4 space-y-1 text-left border-2 border-transparent data-[state=on]:border-primary data-[state=on]:bg-primary/5 hover:bg-muted"
        >
          <div className="flex items-center gap-2 font-semibold">
            <Radio className="h-4 w-4" />
            <span>{t("dashboard.scanForm.modes.mdns.title")}</span>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Info className="h-3 w-3 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>{t("dashboard.scanForm.useMdnsWarning")}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <div className="text-xs text-muted-foreground">
            {t("dashboard.scanForm.modes.mdns.description")}
          </div>
        </ToggleGroupItem>
      </ToggleGroup>
    </div>
  );
}
