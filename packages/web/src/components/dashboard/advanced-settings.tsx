import { useTranslation } from "react-i18next";
import { Settings2, ChevronDown } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { type UseFormReturn } from "react-hook-form";
import { type ScanFormData } from "./scan-form-schema";

interface AdvancedSettingsProps {
  form: UseFormReturn<ScanFormData>;
}

export function AdvancedSettings({ form }: AdvancedSettingsProps) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className="w-full space-y-2"
    >
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="flex items-center gap-2 px-2 hover:bg-transparent text-muted-foreground hover:text-foreground transition-colors"
        >
          <Settings2 className="h-4 w-4" />
          <span className="text-xs font-semibold uppercase tracking-wider">
            {t("dashboard.scanForm.advanced.title", "Advanced Settings")}
          </span>
          <ChevronDown
            className={`h-4 w-4 transition-transform duration-200 ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        </Button>
      </CollapsibleTrigger>

      <CollapsibleContent className="space-y-4 pt-2">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-muted/20 rounded-xl border border-muted-foreground/5">
          <FormField
            control={form.control}
            name="timeout"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-sm font-semibold">
                  {t("dashboard.scanForm.timeout")}
                </FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    min="1"
                    max="600"
                    {...field}
                    onChange={(e) => field.onChange(Number(e.target.value))}
                    className="h-10 bg-background"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="max_workers"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-sm font-semibold">
                  {t("dashboard.scanForm.maxWorkers")}
                </FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    min="1"
                    max="200"
                    {...field}
                    onChange={(e) => field.onChange(Number(e.target.value))}
                    className="h-10 bg-background"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
