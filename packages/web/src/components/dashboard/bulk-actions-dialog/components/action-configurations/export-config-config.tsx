import { useTranslation } from "react-i18next";
import { Upload } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { ActionConfigWrapper } from "./action-config-wrapper";
import type { ExportConfigActionProps } from "../../types";
import { CONFIGURABLE_COMPONENT_TYPES, BULK_ACTION_STYLES } from "../../types";

export function ExportConfigConfig({
  selectedComponentTypes,
  onSelectedComponentTypesChange,
  onExecute,
  onCancel,
}: ExportConfigActionProps) {
  const { t } = useTranslation();

  const handleComponentTypeToggle = (
    componentType: string,
    checked: boolean,
  ) => {
    if (checked) {
      onSelectedComponentTypesChange([
        ...selectedComponentTypes,
        componentType,
      ]);
    } else {
      onSelectedComponentTypesChange(
        selectedComponentTypes.filter((t) => t !== componentType),
      );
    }
  };

  return (
    <ActionConfigWrapper
      title={t("bulkActions.exportConfigurations")}
      icon={<Upload className="h-4 w-4" />}
      onExecute={onExecute}
      onCancel={onCancel}
      isExecuteDisabled={selectedComponentTypes.length === 0}
    >
      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">
            {t("bulkActions.componentSelection")}
          </label>
          <p className="text-sm text-muted-foreground">
            {t("bulkActions.selectComponentTypes")}
          </p>
          <div className={BULK_ACTION_STYLES.componentGrid}>
            {CONFIGURABLE_COMPONENT_TYPES.map((componentType) => (
              <div key={componentType} className="flex items-center space-x-2">
                <Checkbox
                  id={`component-${componentType}`}
                  checked={selectedComponentTypes.includes(componentType)}
                  onCheckedChange={(checked) =>
                    handleComponentTypeToggle(componentType, checked === true)
                  }
                />
                <label
                  htmlFor={`component-${componentType}`}
                  className="text-sm font-medium capitalize"
                >
                  {componentType}
                </label>
              </div>
            ))}
          </div>
        </div>
      </div>
    </ActionConfigWrapper>
  );
}
