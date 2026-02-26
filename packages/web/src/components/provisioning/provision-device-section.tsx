import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import {
  Search,
  Play,
  CheckCircle2,
  XCircle,
  Loader2,
  Radio,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { provisioningApi, handleApiError } from "@/lib/api";
import type { APDeviceInfo, ProvisionResult } from "@/types/api";

export function ProvisionDeviceSection() {
  const { t } = useTranslation();
  const [deviceIp, setDeviceIp] = useState("192.168.33.1");
  const [selectedProfileId, setSelectedProfileId] = useState<
    string | undefined
  >();
  const [detectedDevice, setDetectedDevice] = useState<APDeviceInfo | null>(
    null,
  );
  const [provisionResult, setProvisionResult] =
    useState<ProvisionResult | null>(null);
  const [verifyTargets, setVerifyTargets] = useState("");

  const { data: profiles } = useQuery({
    queryKey: ["provisioning", "profiles"],
    queryFn: provisioningApi.listProfiles,
    enabled: true,
  });

  const detectMutation = useMutation({
    mutationFn: () => provisioningApi.detectDevice(deviceIp),
    onSuccess: (info) => {
      setDetectedDevice(info);
      setProvisionResult(null);
      toast.success(
        t("provisioning.provision.detect.success", {
          app: info.app || info.model,
          generation: info.generation,
        }),
      );
    },
    onError: (err) => {
      setDetectedDevice(null);
      toast.error(handleApiError(err));
    },
  });

  const provisionMutation = useMutation({
    mutationFn: () => {
      const profileId = selectedProfileId
        ? Number(selectedProfileId)
        : undefined;
      return provisioningApi.provisionDevice(deviceIp, profileId);
    },
    onSuccess: (result) => {
      setProvisionResult(result);
      if (result.success) {
        toast.success(t("provisioning.messages.provisionSuccess"));
      } else {
        toast.error(result.error || t("provisioning.messages.provisionFailed"));
      }
    },
    onError: (err) => toast.error(handleApiError(err)),
  });

  const verifyMutation = useMutation({
    mutationFn: () =>
      provisioningApi.verifyProvision(provisionResult?.device_mac || "", [
        verifyTargets,
      ]),
    onSuccess: (result) => {
      if (result.found) {
        toast.success(
          t("provisioning.provision.verify.found", {
            ip: result.device_ip,
          }),
        );
      } else {
        toast.error(t("provisioning.provision.verify.notFound"));
      }
    },
    onError: (err) => toast.error(handleApiError(err)),
  });

  const defaultProfile = profiles?.find((p) => p.is_default);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Radio className="h-5 w-5" />
          <span>{t("provisioning.provision.title")}</span>
        </CardTitle>
        <CardDescription>
          {t("provisioning.provision.description")}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Step 1: Detect */}
        <div className="space-y-3">
          <h4 className="font-medium">
            {t("provisioning.provision.detect.title")}
          </h4>
          <p className="text-sm text-muted-foreground">
            {t("provisioning.provision.detect.description")}
          </p>
          <div className="flex space-x-2">
            <Input
              value={deviceIp}
              onChange={(e) => setDeviceIp(e.target.value)}
              placeholder={t("provisioning.provision.detect.ipPlaceholder")}
              className="max-w-xs font-mono"
            />
            <Button
              onClick={() => detectMutation.mutate()}
              disabled={detectMutation.isPending}
            >
              {detectMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <Search className="h-4 w-4 mr-1" />
              )}
              {t("provisioning.provision.detect.button")}
            </Button>
          </div>

          {detectedDevice && (
            <div className="p-3 rounded-lg border bg-muted/50">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <span className="text-muted-foreground">
                  {t("provisioning.provision.deviceInfo.device")}:
                </span>
                <span className="font-medium">
                  {detectedDevice.app || detectedDevice.model}
                </span>
                <span className="text-muted-foreground">
                  {t("provisioning.provision.deviceInfo.generation")}:
                </span>
                <span>Gen{detectedDevice.generation}</span>
                <span className="text-muted-foreground">
                  {t("provisioning.provision.deviceInfo.mac")}:
                </span>
                <span className="font-mono">{detectedDevice.mac}</span>
                <span className="text-muted-foreground">
                  {t("provisioning.provision.deviceInfo.firmware")}:
                </span>
                <span>{detectedDevice.firmware_version}</span>
                <span className="text-muted-foreground">
                  {t("provisioning.provision.deviceInfo.auth")}:
                </span>
                <span>
                  {detectedDevice.auth_enabled
                    ? t("provisioning.provision.deviceInfo.enabled")
                    : t("provisioning.provision.deviceInfo.disabled")}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Step 2: Select profile & provision */}
        {detectedDevice && !provisionResult && (
          <div className="space-y-3 border-t pt-4">
            <h4 className="font-medium">
              {t("provisioning.provision.selectProfile.title")}
            </h4>
            <div className="space-y-2">
              <Label>{t("provisioning.provision.selectProfile.label")}</Label>
              <Select
                value={selectedProfileId}
                onValueChange={(value) =>
                  setSelectedProfileId(value === "default" ? undefined : value)
                }
              >
                <SelectTrigger className="max-w-xs">
                  <SelectValue
                    placeholder={
                      defaultProfile
                        ? t(
                            "provisioning.provision.selectProfile.defaultLabel",
                            { name: defaultProfile.name },
                          )
                        : t(
                            "provisioning.provision.selectProfile.selectPlaceholder",
                          )
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {defaultProfile && (
                    <SelectItem value="default">
                      {t("provisioning.provision.selectProfile.defaultLabel", {
                        name: defaultProfile.name,
                      })}
                    </SelectItem>
                  )}
                  {profiles?.map((p) => (
                    <SelectItem key={p.id} value={String(p.id)}>
                      {p.name}
                      {p.is_default
                        ? ` (${t("provisioning.profiles.default")})`
                        : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              onClick={() => provisionMutation.mutate()}
              disabled={provisionMutation.isPending}
            >
              {provisionMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-1" />
              )}
              {t("provisioning.provision.selectProfile.button")}
            </Button>
          </div>
        )}

        {/* Step 3: Results */}
        {provisionResult && (
          <div className="space-y-3 border-t pt-4">
            <h4 className="font-medium">
              {t("provisioning.provision.result.title")}
            </h4>
            <div className="space-y-1">
              {provisionResult.steps_completed.map((step, i) => (
                <div key={i} className="flex items-center space-x-2 text-sm">
                  <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
                  <span>
                    <span className="font-medium">{step.name}</span>
                    {step.message && (
                      <span className="text-muted-foreground">
                        {" "}
                        - {step.message}
                      </span>
                    )}
                  </span>
                </div>
              ))}
              {provisionResult.steps_failed.map((step, i) => (
                <div key={i} className="flex items-center space-x-2 text-sm">
                  <XCircle className="h-4 w-4 text-destructive flex-shrink-0" />
                  <span>
                    <span className="font-medium">{step.name}</span>
                    {step.message && (
                      <span className="text-muted-foreground">
                        {" "}
                        - {step.message}
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </div>

            {provisionResult.success && (
              <div className="p-3 rounded-lg border bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800">
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  {t("provisioning.provision.result.success")}
                </p>
                <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                  {provisionResult.device_model} (MAC:{" "}
                  {provisionResult.device_mac})
                </p>
              </div>
            )}

            {!provisionResult.success && (
              <div className="p-3 rounded-lg border bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800">
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  {t("provisioning.provision.result.failed")}
                </p>
                <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                  {provisionResult.error}
                </p>
              </div>
            )}

            {/* Verification */}
            {provisionResult.success && provisionResult.needs_verification && (
              <div className="space-y-3 border-t pt-4">
                <h4 className="font-medium">
                  {t("provisioning.provision.verify.title")}
                </h4>
                <p className="text-sm text-muted-foreground">
                  {t("provisioning.provision.verify.description")}
                </p>
                <div className="flex space-x-2">
                  <Input
                    value={verifyTargets}
                    onChange={(e) => setVerifyTargets(e.target.value)}
                    placeholder={t(
                      "provisioning.provision.verify.networkPlaceholder",
                    )}
                    className="max-w-xs font-mono"
                  />
                  <Button
                    onClick={() => verifyMutation.mutate()}
                    disabled={verifyMutation.isPending || !verifyTargets}
                    variant="outline"
                  >
                    {verifyMutation.isPending ? (
                      <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    ) : (
                      <Search className="h-4 w-4 mr-1" />
                    )}
                    {t("provisioning.provision.verify.button")}
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
