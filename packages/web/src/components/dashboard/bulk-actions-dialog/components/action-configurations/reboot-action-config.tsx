import { useTranslation } from "react-i18next";
import { Power } from "lucide-react";
import { ActionConfigWrapper } from "./action-config-wrapper";
import type { BaseActionConfigProps } from "../../types";

export function RebootActionConfig({
  onExecute,
  onCancel,
}: BaseActionConfigProps) {
  const { t } = useTranslation();

  return (
    <ActionConfigWrapper
      title={t("bulkActions.rebootDevices")}
      icon={<Power className="h-4 w-4" />}
      onExecute={onExecute}
      onCancel={onCancel}
    >
      <div className="text-sm text-muted-foreground">
        {t("bulkActions.descriptions.rebootDevices")}
      </div>
    </ActionConfigWrapper>
  );
}
