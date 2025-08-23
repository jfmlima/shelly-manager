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
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
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
  useActionResponseModal,
  getActionDisplayName,
  getActionIcon,
  isDestructiveAction,
  isComingSoonAction,
} from "@/hooks/useComponentActions";
import {
  shouldShowResponseData,
  hasResponseData,
  getComponentKeyForAction,
} from "@/utils/action-responses";
import { ActionResponseModal } from "./action-response-modal";
import { SetConfigModal } from "./set-config-modal";
import type { Component } from "@/types/api";

interface ComponentActionsProps {
  component: Component;
  deviceIp: string;
}

const PRIORITY_ACTION_PATTERNS = [
  /^(.*\.)?Get/,
  /^(.*\.)?Set/,
  /^(.*\.)?Reboot$/,
  /^(.*\.)?FactoryReset$/,
  /^(.*\.)?Toggle$/,
  /^(.*\.)?Connect$/,
  /^(.*\.)?Disconnect$/,
  /^(.*\.)?Update$/,
  /^(.*\.)?Open$/,
  /^(.*\.)?Close$/,
];

const MAX_VISIBLE_ACTIONS = 10;

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

function getActionPriorityScore(action: string): number {
  for (let i = 0; i < PRIORITY_ACTION_PATTERNS.length; i++) {
    if (PRIORITY_ACTION_PATTERNS[i].test(action)) {
      return i;
    }
  }
  return PRIORITY_ACTION_PATTERNS.length;
}

function sortActionsByPriority(actions: string[]): string[] {
  return [...actions].sort((a, b) => {
    const scoreA = getActionPriorityScore(a);
    const scoreB = getActionPriorityScore(b);

    if (scoreA !== scoreB) {
      return scoreA - scoreB;
    }

    return a.localeCompare(b);
  });
}

export function ComponentActions({
  component,
  deviceIp,
}: ComponentActionsProps) {
  const { t } = useTranslation();
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [actionParameters, setActionParameters] = useState<
    Record<string, unknown>
  >({});
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [showAllActions, setShowAllActions] = useState(false);
  const [showSetConfigModal, setShowSetConfigModal] = useState(false);

  const { responseModalState, openResponseModal, closeResponseModal } =
    useActionResponseModal();

  const executeAction = useExecuteComponentAction({
    onResponseReceived: (response) => {
      if (
        shouldShowResponseData(selectedAction || "") &&
        hasResponseData(response)
      ) {
        openResponseModal(response);
      }
    },
  });

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

  const sortedActions = sortActionsByPriority(component.available_actions);
  const priorityActions = sortedActions.slice(0, MAX_VISIBLE_ACTIONS);
  const additionalActions = sortedActions.slice(MAX_VISIBLE_ACTIONS);
  const hasAdditionalActions = additionalActions.length > 0;

  const handleActionClick = (action: string) => {
    setSelectedAction(action);
    setActionParameters({});

    if (action.includes("SetConfig")) {
      setShowSetConfigModal(true);
      return;
    }

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
    const correctComponentKey = getComponentKeyForAction(action, component);

    executeAction.mutate(
      {
        deviceIp,
        componentKey: correctComponentKey,
        action,
        parameters,
      },
      {
        onSuccess: () => {
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
    const isComingSoon = isComingSoonAction(action);

    if (isComingSoon) {
      return (
        <div key={action} className="relative group">
          <Button
            variant={isDestructive ? "destructive" : "outline"}
            size="sm"
            onClick={() => {}}
            disabled={true}
            className="flex items-center space-x-2 opacity-60 cursor-not-allowed"
          >
            <IconComponent className="h-3 w-3" />
            <span>{getActionDisplayName(action)}</span>
          </Button>
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
            {t("common.comingSoon")}
          </div>
        </div>
      );
    }

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

      <div className="space-y-3">
        {/* Always visible priority actions */}
        <div className="flex flex-wrap gap-2">
          {priorityActions.map((action) => renderActionButton(action))}
        </div>

        {/* Collapsible additional actions */}
        {hasAdditionalActions && (
          <Collapsible open={showAllActions} onOpenChange={setShowAllActions}>
            <CollapsibleContent>
              <div className="flex flex-wrap gap-2 pt-2">
                {additionalActions.map((action) => renderActionButton(action))}
              </div>
            </CollapsibleContent>

            <div className="flex justify-center pt-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAllActions(!showAllActions)}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                {showAllActions ? (
                  <>
                    <ChevronUp className="mr-1 h-3 w-3" />
                    {t("componentActions.showFewerActions")}
                  </>
                ) : (
                  <>
                    <ChevronDown className="mr-1 h-3 w-3" />
                    {t("componentActions.showMoreActions", {
                      count: additionalActions.length,
                    })}
                  </>
                )}
              </Button>
            </div>
          </Collapsible>
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

      {/* Action Response Modal */}
      <ActionResponseModal
        isOpen={responseModalState.isOpen}
        onClose={closeResponseModal}
        response={responseModalState.response}
        componentType={component.type}
      />

      {/* SetConfig Modal */}
      <SetConfigModal
        isOpen={showSetConfigModal}
        onClose={() => setShowSetConfigModal(false)}
        component={component}
        deviceIp={deviceIp}
      />
    </div>
  );
}
