import { zodResolver } from "@hookform/resolvers/zod";
import type { ScanRequest } from "@/types/api"; // Added back
import type { ScanPreferences } from "@/lib/scan-preferences"; // Added back
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useEffect, useRef } from "react";
import { Search } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { credentialsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { parseManualIPs } from "@/lib/ip-utils";
import {
  loadScanPreferences,
  saveScanPreferences,
} from "@/lib/scan-preferences";
import { ScanModeSelector } from "./scan-mode-selector";
import { ManualDiscoveryPanel } from "./manual-discovery-panel";
import { AdvancedSettings } from "./advanced-settings";
import { Checkbox } from "@/components/ui/checkbox";
import { CredentialsManager } from "./credentials-manager";

import { scanFormSchema, type ScanFormData } from "./scan-form-schema";

interface ScanFormProps {
  onSubmit: (data: ScanRequest) => void;
  isLoading?: boolean;
}

export function ScanForm({ onSubmit, isLoading = false }: ScanFormProps) {
  const { t } = useTranslation();

  const form = useForm<ScanFormData>({
    resolver: zodResolver(scanFormSchema),
    defaultValues: {
      ...loadScanPreferences(),
      use_auth: false, // Always default to false, don't persist this
    } as ScanFormData,
  });

  const scanMode = form.watch("scan_mode");
  const useAuth = form.watch("use_auth");

  // Load credentials when authentication is enabled
  const credentialsQuery = useQuery({
    queryKey: ["credentials"],
    queryFn: credentialsApi.listCredentials,
    enabled: useAuth, // Only fetch when authentication is enabled
    staleTime: 0, // Always refetch to ensure fresh data
  });
  const timeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  useEffect(() => {
    const subscription = form.watch((value) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        // Don't save use_auth - it should always default to false
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { use_auth, ...prefsToSave } =
          value as unknown as ScanPreferences & { use_auth: boolean };
        saveScanPreferences(prefsToSave);
      }, 1000); // Debounce for 1 second
    });

    return () => {
      subscription.unsubscribe();
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [form]);

  const handleSubmit = (data: ScanFormData) => {
    const targets: string[] = [];

    if (data.scan_mode === "manual") {
      if (data.manual_mode === "ips" && data.manual_ips) {
        targets.push(...parseManualIPs(data.manual_ips));
      } else if (data.manual_mode === "range_cidr" && data.range_cidr) {
        targets.push(data.range_cidr.trim());
      }
    }

    onSubmit({
      targets,
      use_mdns: data.scan_mode === "mdns",
      timeout: data.timeout,
      max_workers: data.max_workers,
    });
  };

  return (
    <Card className="border-shadow-sm">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center space-x-2.5 text-xl font-bold">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Search className="h-5 w-5 text-primary" />
          </div>
          <span>{t("dashboard.scanForm.title")}</span>
        </CardTitle>
        <CardDescription className="text-sm">
          {t("dashboard.scanForm.description")}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(handleSubmit)}
            className="space-y-6"
          >
            <FormField
              control={form.control}
              name="scan_mode"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <ScanModeSelector
                      value={field.value}
                      onValueChange={(v) => field.onChange(v)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {scanMode === "manual" && (
              <div className="p-4 bg-muted/30 rounded-xl border border-muted-foreground/10">
                <ManualDiscoveryPanel
                  manualMode={form.watch("manual_mode")}
                  manualIPs={form.watch("manual_ips") || ""}
                  rangeCIDR={form.watch("range_cidr") || ""}
                  onManualModeChange={(v) => form.setValue("manual_mode", v)}
                  onManualIPsChange={(v) => form.setValue("manual_ips", v)}
                  onRangeCIDRChange={(v) => form.setValue("range_cidr", v)}
                />
                <FormField
                  name="manual_ips"
                  render={() => <FormMessage className="mt-2" />}
                />
                <FormField
                  name="range_cidr"
                  render={() => <FormMessage className="mt-2" />}
                />
              </div>
            )}

            <AdvancedSettings form={form} />

            <div className="p-4 bg-muted/30 rounded-xl border border-muted-foreground/10 space-y-4">
              <FormField
                control={form.control}
                name="use_auth"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <div className="space-y-1 leading-none">
                      <FormLabel className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                        {t("dashboard.scanForm.credentials.enableAuth")}
                      </FormLabel>
                      <p className="text-xs text-muted-foreground">
                        {t(
                          "dashboard.scanForm.credentials.enableAuthDescription",
                        )}
                      </p>
                    </div>
                  </FormItem>
                )}
              />

              {useAuth && (
                <div className="pt-2 border-t border-muted-foreground/10">
                  <CredentialsManager
                    credentials={credentialsQuery.data || []}
                    isLoading={
                      credentialsQuery.isLoading || credentialsQuery.isFetching
                    }
                  />
                </div>
              )}
            </div>

            <div className="pt-2">
              <Button
                type="submit"
                disabled={isLoading}
                className="w-full h-11 text-base font-semibold transition-all hover:scale-[1.01]"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-current mr-3" />
                    {t("dashboard.scanForm.scanning")}
                  </>
                ) : (
                  <>
                    <Search className="h-5 w-5 mr-3" />
                    {t("dashboard.scanForm.scanButton")}
                  </>
                )}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
