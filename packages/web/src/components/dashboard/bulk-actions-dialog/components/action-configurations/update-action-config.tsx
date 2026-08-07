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
import type { UpdateSource } from "@/types/api";

export function UpdateActionConfig({
  updateChannel,
  onUpdateChannelChange,
  updateSource,
  onUpdateSourceChange,
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
          {t("deviceDetail.dialogs.updateFirmware.updateSource")}
        </label>
        <Select
          value={updateSource}
          onValueChange={(value: UpdateSource) => onUpdateSourceChange(value)}
        >
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="internet">
              {t("deviceDetail.dialogs.updateFirmware.sourceInternet")}
            </SelectItem>
            <SelectItem value="local">
              {t("deviceDetail.dialogs.updateFirmware.sourceLocal")}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
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
