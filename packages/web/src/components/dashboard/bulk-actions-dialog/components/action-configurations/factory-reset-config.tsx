import { useTranslation } from "react-i18next";
import { AlertCircle } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { ActionConfigWrapper } from "./action-config-wrapper";
import type { FactoryResetConfigProps } from "../../types";
import { BULK_ACTION_STYLES } from "../../types";

export function FactoryResetConfig({
  confirmFactoryReset,
  onConfirmFactoryResetChange,
  onExecute,
  onCancel,
}: FactoryResetConfigProps) {
  const { t } = useTranslation();

  return (
    <ActionConfigWrapper
      title={t("bulkActions.factoryReset")}
      icon={<AlertCircle className="h-4 w-4" />}
      onExecute={onExecute}
      onCancel={onCancel}
      isExecuteDisabled={!confirmFactoryReset}
    >
      <div className={`space-y-4 ${BULK_ACTION_STYLES.warningBox}`}>
        <div className="flex items-center space-x-2">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <span className="font-medium text-destructive">
            {t("bulkActions.warnings.factoryReset")}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">
          {t("bulkActions.warnings.factoryResetDescription")}
        </p>
        <div className="flex items-center space-x-2">
          <Checkbox
            id="confirm-factory-reset"
            checked={confirmFactoryReset}
            onCheckedChange={(checked) =>
              onConfirmFactoryResetChange(checked === true)
            }
          />
          <label
            htmlFor="confirm-factory-reset"
            className="text-sm font-medium"
          >
            {t("bulkActions.confirmFactoryReset")}
          </label>
        </div>
      </div>
    </ActionConfigWrapper>
  );
}
