import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Power,
  Download,
  AlertTriangle,
  Clock,
  ToggleLeft,
  Settings,
  RotateCcw,
  ChevronUp,
  ChevronDown,
  Square,
  Target,
  Radio,
  Trash2,
  Info,
  Wifi,
  WifiOff,
  Play,
  Loader2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";

import {
  useExecuteComponentAction,
  getActionDisplayName,
  getActionIcon,
  isDestructiveAction,
} from "@/hooks/useComponentActions";
import type { Component } from "@/types/api";

interface ComponentActionsProps {
  component: Component;
  deviceIp: string;
  onActionExecuted?: () => void;
}

const iconComponents = {
  Power,
  Download,
  AlertTriangle,
  Clock,
  ToggleLeft,
  Settings,
  RotateCcw,
  ChevronUp,
  ChevronDown,
  Square,
  Target,
  Radio,
  Trash2,
  Info,
  Wifi,
  WifiOff,
  Play,
};

export function ComponentActions({
  component,
  deviceIp,
  onActionExecuted,
}: ComponentActionsProps) {
  const { t } = useTranslation();
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [actionParameters, setActionParameters] = useState<
    Record<string, unknown>
  >({});
  const [showConfirmation, setShowConfirmation] = useState(false);

  const executeAction = useExecuteComponentAction();

  if (
    !component.available_actions ||
    component.available_actions.length === 0
  ) {
    return (
      <div className="text-sm text-muted-foreground">
        {t("componentActions.noActionsAvailable")}
      </div>
    );
  }

  const handleActionClick = (action: string) => {
    setSelectedAction(action);
    setActionParameters({});

    if (isDestructiveAction(action)) {
      setShowConfirmation(true);
    } else {
      executeActionWithParameters(action, {});
    }
  };

  const executeActionWithParameters = (
    action: string,
    parameters: Record<string, unknown>,
  ) => {
    executeAction.mutate(
      {
        deviceIp,
        componentKey: component.key,
        action,
        parameters,
      },
      {
        onSuccess: () => {
          onActionExecuted?.();
          setSelectedAction(null);
          setShowConfirmation(false);
        },
      },
    );
  };

  const renderActionButton = (action: string) => {
    const IconComponent =
      iconComponents[getActionIcon(action) as keyof typeof iconComponents] ||
      Play;
    const isLoading = executeAction.isPending && selectedAction === action;
    const isDestructive = isDestructiveAction(action);

    return (
      <Button
        key={action}
        variant={isDestructive ? "destructive" : "outline"}
        size="sm"
        onClick={() => handleActionClick(action)}
        disabled={executeAction.isPending}
        className="flex items-center space-x-2"
      >
        {isLoading ? (
          <Loader2 className="h-3 w-3 animate-spin" />
        ) : (
          <IconComponent className="h-3 w-3" />
        )}
        <span>{getActionDisplayName(action)}</span>
      </Button>
    );
  };

  const renderParameterForm = (action: string) => {
    const cleanAction = action.includes(".")
      ? action.split(".").pop() || action
      : action;

    switch (cleanAction) {
      case "Set":
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="output">Switch State</Label>
              <Select
                value={actionParameters.output?.toString() || ""}
                onValueChange={(value) =>
                  setActionParameters({
                    ...actionParameters,
                    output: value === "true",
                  })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select state" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">On</SelectItem>
                  <SelectItem value="false">Off</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case "GoToPosition":
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="position">Position (0-100)</Label>
              <Input
                id="position"
                type="number"
                min="0"
                max="100"
                value={actionParameters.pos?.toString() || ""}
                onChange={(e) =>
                  setActionParameters({
                    ...actionParameters,
                    pos: parseInt(e.target.value),
                  })
                }
                placeholder="Enter position"
              />
            </div>
          </div>
        );

      case "Update":
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="channel">Update Channel</Label>
              <Select
                value={(actionParameters.channel as string) || "stable"}
                onValueChange={(value) =>
                  setActionParameters({ ...actionParameters, channel: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="stable">Stable</SelectItem>
                  <SelectItem value="beta">Beta</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">{t("componentActions.title")}</h4>
        <Badge variant="outline" className="text-xs">
          {component.available_actions.length} {t("componentActions.available")}
        </Badge>
      </div>

      <div className="flex flex-wrap gap-2">
        {component.available_actions.map((action) =>
          renderActionButton(action),
        )}
      </div>

      {/* Confirmation Dialog for Destructive Actions */}
      <Dialog open={showConfirmation} onOpenChange={setShowConfirmation}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Action</DialogTitle>
            <DialogDescription>
              {selectedAction && (
                <>
                  Are you sure you want to execute "
                  {getActionDisplayName(selectedAction)}" on this component?
                  {isDestructiveAction(selectedAction) && (
                    <Alert className="mt-4">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        This is a destructive action and cannot be undone.
                      </AlertDescription>
                    </Alert>
                  )}
                </>
              )}
            </DialogDescription>
          </DialogHeader>

          {selectedAction && renderParameterForm(selectedAction)}

          <div className="flex space-x-2 mt-4">
            <Button
              onClick={() => {
                if (selectedAction) {
                  executeActionWithParameters(selectedAction, actionParameters);
                }
              }}
              disabled={executeAction.isPending}
            >
              {executeAction.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Executing...
                </>
              ) : (
                "Confirm"
              )}
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setShowConfirmation(false);
                setSelectedAction(null);
              }}
              disabled={executeAction.isPending}
            >
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
