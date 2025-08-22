import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ActionConfigWrapperProps {
  title: string;
  icon: ReactNode;
  children: ReactNode;
  onExecute: () => void;
  onCancel: () => void;
  isExecuteDisabled?: boolean;
}

export function ActionConfigWrapper({
  title,
  icon,
  children,
  onExecute,
  onCancel,
  isExecuteDisabled = false,
}: ActionConfigWrapperProps) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          {icon}
          <span>{title}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {children}

        <div className="flex space-x-2">
          <Button onClick={onExecute} disabled={isExecuteDisabled}>
            {t("common.confirm")}
          </Button>
          <Button variant="outline" onClick={onCancel}>
            {t("common.cancel")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
