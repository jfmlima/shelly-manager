import { useTranslation } from "react-i18next";
import { Download } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ActionConfigWrapper } from "./action-config-wrapper";
import type { UpdateActionConfigProps } from "../../types";

export function UpdateActionConfig({
  updateChannel,
  onUpdateChannelChange,
  onExecute,
  onCancel,
}: UpdateActionConfigProps) {
  const { t } = useTranslation();

  return (
    <ActionConfigWrapper
      title={t("bulkActions.updateFirmware")}
      icon={<Download className="h-4 w-4" />}
      onExecute={onExecute}
      onCancel={onCancel}
    >
      <div className="space-y-2">
        <label className="text-sm font-medium">
          {t("bulkActions.channel")}
        </label>
        <Select value={updateChannel} onValueChange={onUpdateChannelChange}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="stable">{t("bulkActions.stable")}</SelectItem>
            <SelectItem value="beta">{t("bulkActions.beta")}</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </ActionConfigWrapper>
  );
}
