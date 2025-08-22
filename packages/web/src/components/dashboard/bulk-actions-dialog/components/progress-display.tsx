import { useTranslation } from "react-i18next";
import { CheckCircle, XCircle, ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Progress } from "@/components/ui/progress";
import type { ProgressDisplayProps } from "../types";
import { BULK_ACTION_STYLES } from "../types";

export function ProgressDisplay({
  progress,
  showDetails,
  onShowDetailsChange,
  onClose,
  onReset,
}: ProgressDisplayProps) {
  const { t } = useTranslation();

  const getResultIcon = (success: boolean) => {
    return success ? (
      <CheckCircle className="h-4 w-4 text-green-600" />
    ) : (
      <XCircle className="h-4 w-4 text-red-600" />
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("bulkActions.progress")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>{t("bulkActions.overallProgress")}</span>
            <span>
              {progress.completed + progress.failed} / {progress.total}
            </span>
          </div>
          <Progress
            value={
              ((progress.completed + progress.failed) / progress.total) * 100
            }
            className="w-full"
          />
        </div>

        <div className={BULK_ACTION_STYLES.progressGrid}>
          <div>
            <div className="text-2xl font-bold text-green-600">
              {progress.completed}
            </div>
            <div className="text-sm text-muted-foreground">
              {t("bulkActions.successful")}
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-600">
              {progress.failed}
            </div>
            <div className="text-sm text-muted-foreground">
              {t("bulkActions.failed")}
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold">
              {progress.total - progress.completed - progress.failed}
            </div>
            <div className="text-sm text-muted-foreground">
              {t("bulkActions.pending")}
            </div>
          </div>
        </div>

        {progress.results.length > 0 && (
          <Collapsible open={showDetails} onOpenChange={onShowDetailsChange}>
            <CollapsibleTrigger asChild>
              <Button variant="outline" className="w-full">
                <span>{t("bulkActions.viewDetails")}</span>
                {showDetails ? (
                  <ChevronDown className="ml-2 h-4 w-4" />
                ) : (
                  <ChevronRight className="ml-2 h-4 w-4" />
                )}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-2 mt-4">
              {progress.results.map((result) => (
                <div
                  key={result.ip}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    {getResultIcon(result.success)}
                    <span className="font-mono text-sm">{result.ip}</span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {result.success ? result.message : result.error}
                  </div>
                </div>
              ))}
            </CollapsibleContent>
          </Collapsible>
        )}

        {!progress.isRunning && (
          <div className="flex space-x-2">
            <Button onClick={onClose}>{t("common.close")}</Button>
            <Button variant="outline" onClick={onReset}>
              {t("bulkActions.startNewAction")}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
