import { useTranslation } from "react-i18next";
import { Download, AlertCircle } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ActionConfigWrapper } from "./action-config-wrapper";
import type { ApplyConfigActionProps } from "../../types";
import { CONFIGURABLE_COMPONENT_TYPES, BULK_ACTION_STYLES } from "../../types";

export function ApplyConfigConfig({
  selectedComponentType,
  onSelectedComponentTypeChange,
  configurationJson,
  onConfigurationJsonChange,
  configError,
  onExecute,
  onCancel,
}: ApplyConfigActionProps) {
  const { t } = useTranslation();

  const isExecuteDisabled = !selectedComponentType || !configurationJson.trim();

  return (
    <ActionConfigWrapper
      title={t("bulkActions.applyConfiguration")}
      icon={<Download className="h-4 w-4" />}
      onExecute={onExecute}
      onCancel={onCancel}
      isExecuteDisabled={isExecuteDisabled}
    >
      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">
            {t("bulkActions.componentSelection")}
          </label>
          <p className="text-sm text-muted-foreground">
            {t("bulkActions.selectSingleComponentType")}
          </p>
          <Select
            value={selectedComponentType}
            onValueChange={onSelectedComponentTypeChange}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select component type" />
            </SelectTrigger>
            <SelectContent>
              {CONFIGURABLE_COMPONENT_TYPES.map((componentType) => (
                <SelectItem key={componentType} value={componentType}>
                  <span className="capitalize">{componentType}</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">
            {t("bulkActions.configurationEditor")}
          </label>
          <p className="text-sm text-muted-foreground">
            {t("bulkActions.pasteJsonConfig")}
          </p>
          <textarea
            className="w-full h-32 p-3 border rounded-lg font-mono text-sm"
            placeholder={`{
  "in_mode": "flip",
  "initial_state": "restore_last"
}`}
            value={configurationJson}
            onChange={(e) => onConfigurationJsonChange(e.target.value)}
          />
          {configError && <p className="text-sm text-red-600">{configError}</p>}
        </div>

        {selectedComponentType && (
          <div className={BULK_ACTION_STYLES.infoBox}>
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              <span className="font-medium text-blue-800">
                {t("bulkActions.configurationDiff")}
              </span>
            </div>
            <p className="text-sm text-blue-700 mt-2">
              {t("bulkActions.applyToComponents", {
                componentType: selectedComponentType,
              })}
            </p>
          </div>
        )}

        <div className={BULK_ACTION_STYLES.safetyBox}>
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-orange-600" />
            <span className="font-medium text-orange-800">
              {t("bulkActions.safetyWarning")}
            </span>
          </div>
          <p className="text-sm text-orange-700 mt-2">
            {t("bulkActions.backupResponsibility")}
          </p>
        </div>
      </div>
    </ActionConfigWrapper>
  );
}
