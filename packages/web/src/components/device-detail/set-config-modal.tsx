import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Settings, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  JsonConfigEditor,
  useConfiguration,
} from "@/components/shared/configuration";
import { useExecuteComponentAction } from "@/hooks/useComponentActions";
import type { Component } from "@/types/api";

interface SetConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  component: Component;
  deviceIp: string;
}

export function SetConfigModal({
  isOpen,
  onClose,
  component,
  deviceIp,
}: SetConfigModalProps) {
  const { t } = useTranslation();
  const [isLoadingCurrent, setIsLoadingCurrent] = useState(false);

  const componentType = component.key.includes(":")
    ? component.key.split(":")[0]
    : component.type || "generic";

  const configuration = useConfiguration({
    componentType,
  });

  const executeAction = useExecuteComponentAction({
    onResponseReceived: () => {},
  });

  useEffect(() => {
    if (!isOpen) {
      configuration.reset();
    }
  }, [isOpen, configuration]);

  const handleLoadCurrentConfig = async () => {
    if (!component.available_actions?.includes("GetConfig")) {
      toast.error(
        t(
          "componentActions.setConfig.getConfigNotAvailable",
          "GetConfig is not available for this component",
        ),
      );
      return;
    }

    setIsLoadingCurrent(true);
    try {
      const result = await executeAction.mutateAsync({
        deviceIp,
        componentKey: component.key,
        action: "GetConfig",
        parameters: {},
      });

      if (result.success && result.data) {
        configuration.loadFromObject(result.data);
        toast.success(
          t(
            "componentActions.setConfig.loadSuccess",
            "Current configuration loaded successfully",
          ),
        );
      } else {
        toast.error(
          result.error ||
            t(
              "componentActions.setConfig.loadError",
              "Failed to load current configuration",
            ),
        );
      }
    } catch {
      toast.error(
        t(
          "componentActions.setConfig.loadError",
          "Failed to load current configuration",
        ),
      );
    } finally {
      setIsLoadingCurrent(false);
    }
  };

  const handleApplyConfig = async () => {
    if (!configuration.isValid || !configuration.parsedValue) {
      toast.error(
        t(
          "componentActions.setConfig.invalidConfig",
          "Please fix the configuration errors before applying",
        ),
      );
      return;
    }

    try {
      const result = await executeAction.mutateAsync({
        deviceIp,
        componentKey: component.key,
        action: "SetConfig",
        parameters: { config: configuration.parsedValue },
      });

      if (result.success) {
        toast.success(
          t(
            "componentActions.setConfig.applySuccess",
            "Configuration applied successfully",
          ),
        );
        onClose();
      } else {
        toast.error(
          result.error ||
            t(
              "componentActions.setConfig.applyError",
              "Failed to apply configuration",
            ),
        );
      }
    } catch {
      toast.error(
        t(
          "componentActions.setConfig.applyError",
          "Failed to apply configuration",
        ),
      );
    }
  };

  const isExecuting = executeAction.isPending;
  const canApply = configuration.isValid && configuration.value.trim() !== "";

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>
              {t("componentActions.setConfig.title", "Configure Component")}
            </span>
          </DialogTitle>
          <DialogDescription>
            {t(
              "componentActions.setConfig.modalDescription",
              "Configure the settings for {{componentKey}}. You can load the current configuration and modify only the fields you want to change.",
              { componentKey: component.key },
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Load Current Configuration Section */}
          {component.available_actions?.includes("GetConfig") && (
            <div className="p-4 bg-muted rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">
                    {t(
                      "componentActions.setConfig.currentConfig",
                      "Current Configuration",
                    )}
                  </h4>
                  <p className="text-sm text-muted-foreground">
                    {t(
                      "componentActions.setConfig.loadCurrentDescription",
                      "Load the current component configuration as a starting point",
                    )}
                  </p>
                </div>
                <Button
                  variant="outline"
                  onClick={handleLoadCurrentConfig}
                  disabled={isLoadingCurrent || isExecuting}
                >
                  {isLoadingCurrent ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      {t("common.loading", "Loading...")}
                    </>
                  ) : (
                    <>
                      <Settings className="h-4 w-4 mr-2" />
                      {t(
                        "componentActions.setConfig.loadCurrent",
                        "Load Current",
                      )}
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* Configuration Editor */}
          <JsonConfigEditor
            value={configuration.value}
            onChange={configuration.setValue}
            label={t(
              "componentActions.setConfig.label",
              "Configuration (JSON)",
            )}
            description={t(
              "componentActions.setConfig.description",
              "Enter the component configuration as JSON. Only changed fields need to be included.",
            )}
            examples={configuration.examples}
            placeholder={`{
  "enable": true,
  "name": "${component.config?.name || `${componentType} ${component.id || 0}`}"
}`}
            disabled={isExecuting}
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isExecuting}>
            {t("common.cancel", "Cancel")}
          </Button>
          <Button
            onClick={handleApplyConfig}
            disabled={!canApply || isExecuting}
          >
            {isExecuting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {t("componentActions.setConfig.applying", "Applying...")}
              </>
            ) : (
              t("componentActions.setConfig.apply", "Apply Configuration")
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
