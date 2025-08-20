import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { deviceApi } from "@/lib/api";
import type { ComponentActionResult } from "@/types/api";

interface ExecuteComponentActionParams {
  deviceIp: string;
  componentKey: string;
  action: string;
  parameters?: Record<string, unknown>;
}

export function useExecuteComponentAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      deviceIp,
      componentKey,
      action,
      parameters,
    }: ExecuteComponentActionParams): Promise<ComponentActionResult> => {
      const cleanAction = action.includes(".")
        ? action.split(".").pop() || action
        : action;

      return deviceApi.executeComponentAction(
        deviceIp,
        componentKey,
        cleanAction,
        parameters,
      );
    },
    onSuccess: (result, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["device", "status", variables.deviceIp],
      });

      if (result.success) {
        toast.success(
          result.message || `Action ${variables.action} executed successfully`,
        );
      } else {
        toast.error(result.error || `Action ${variables.action} failed`);
      }
    },
    onError: (error, variables) => {
      toast.error(`Failed to execute ${variables.action}: ${error}`);
    },
  });
}

export function getActionDisplayName(action: string): string {
  const cleanAction = action.includes(".")
    ? action.split(".").pop() || action
    : action;

  const actionMap: Record<string, string> = {
    // System actions
    Reboot: "Reboot Device",
    Update: "Update Firmware",
    FactoryReset: "Factory Reset",
    SetTime: "Set Time",

    // Switch actions
    Toggle: "Toggle",
    Set: "Set State",
    ResetCounters: "Reset Counters",
    GetStatus: "Get Status",

    // Cover actions
    Open: "Open",
    Close: "Close",
    Stop: "Stop",
    GoToPosition: "Go to Position",

    // Zigbee actions
    StartNetworkSteering: "Start Pairing",
    ClearNetwork: "Clear Network",

    // Input actions
    SetConfig: "Update Config",

    // Cloud actions
    Connect: "Connect",
    Disconnect: "Disconnect",
  };

  return actionMap[cleanAction] || cleanAction;
}

export function getActionIcon(action: string): string {
  const cleanAction = action.includes(".")
    ? action.split(".").pop() || action
    : action;

  const iconMap: Record<string, string> = {
    // System actions
    Reboot: "Power",
    Update: "Download",
    FactoryReset: "AlertTriangle",
    SetTime: "Clock",

    // Switch actions
    Toggle: "ToggleLeft",
    Set: "Settings",
    ResetCounters: "RotateCcw",
    GetStatus: "Info",

    // Cover actions
    Open: "ChevronUp",
    Close: "ChevronDown",
    Stop: "Square",
    GoToPosition: "Target",

    // Zigbee actions
    StartNetworkSteering: "Radio",
    ClearNetwork: "Trash2",

    // Input actions
    SetConfig: "Settings",

    // Cloud actions
    Connect: "Wifi",
    Disconnect: "WifiOff",
  };

  return iconMap[cleanAction] || "Play";
}

export function isDestructiveAction(action: string): boolean {
  const cleanAction = action.includes(".")
    ? action.split(".").pop() || action
    : action;

  const destructiveActions = ["Reboot", "FactoryReset", "ClearNetwork"];
  return destructiveActions.includes(cleanAction);
}
