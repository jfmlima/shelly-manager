import { useTranslation } from "react-i18next";
import { Power, Download, Upload, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type {
  ActionSelectionProps,
  BulkActionType,
  ActionCardData,
} from "../types";
import { BULK_ACTION_STYLES } from "../types";

export function ActionSelection({ onActionSelect }: ActionSelectionProps) {
  const { t } = useTranslation();

  const actionCards: ActionCardData[] = [
    {
      id: "update" as BulkActionType,
      titleKey: "bulkActions.updateFirmware",
      descriptionKey: "bulkActions.descriptions.updateFirmware",
      icon: <Download className="h-6 w-6" />,
    },
    {
      id: "reboot" as BulkActionType,
      titleKey: "bulkActions.rebootDevices",
      descriptionKey: "bulkActions.descriptions.rebootDevices",
      icon: <Power className="h-6 w-6" />,
    },
    {
      id: "factory_reset" as BulkActionType,
      titleKey: "bulkActions.factoryReset",
      descriptionKey: "bulkActions.descriptions.factoryReset",
      icon: <AlertCircle className="h-6 w-6" />,
    },
    {
      id: "export_config" as BulkActionType,
      titleKey: "bulkActions.exportConfigurations",
      descriptionKey: "bulkActions.descriptions.exportConfigurations",
      icon: <Upload className="h-6 w-6" />,
    },
    {
      id: "apply_config" as BulkActionType,
      titleKey: "bulkActions.applyConfiguration",
      descriptionKey: "bulkActions.descriptions.applyConfiguration",
      icon: <Download className="h-6 w-6" />,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {actionCards.map((action) => {
        const isComingSoon = action.isComingSoon;
        const isDangerous = action.id === "factory_reset";

        return (
          <Card
            key={action.id}
            className={`${BULK_ACTION_STYLES.actionCard} ${
              isComingSoon
                ? BULK_ACTION_STYLES.disabledCard
                : isDangerous
                  ? BULK_ACTION_STYLES.dangerCard
                  : ""
            }`}
            onClick={() => !isComingSoon && onActionSelect(action.id)}
          >
            <CardHeader>
              <CardTitle className="flex items-center space-x-3">
                {action.icon}
                <span>{t(action.titleKey)}</span>
              </CardTitle>
              {isComingSoon && (
                <Badge variant="secondary" className="text-xs w-fit mb-2 mt-2">
                  {t("common.comingSoon")}
                </Badge>
              )}
              <CardDescription>
                {isComingSoon
                  ? t("bulkActions.comingSoonDescription")
                  : t(action.descriptionKey)}
              </CardDescription>
            </CardHeader>
          </Card>
        );
      })}
    </div>
  );
}
