import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { deviceApi } from "@/lib/api";
import type { ComponentActionResult } from "@/types/api";

const GET_ACTIONS = [
  "GetStatus",
  "GetConfig",
  "GetInfo",
  "GetDeviceInfo",
  "GetComponents",
  "ListMethods",
  "CheckForUpdate",
  "GetCustomMethods",
  "DetectLocation",
  "Scan",
  "ListAPClients",
];

interface ExecuteComponentActionParams {
  deviceIp: string;
  componentKey: string;
  action: string;
  parameters?: Record<string, unknown>;
}

interface UseActionResponseModalResult {
  responseModalState: {
    isOpen: boolean;
    response: ComponentActionResult | null;
  };
  openResponseModal: (response: ComponentActionResult) => void;
  closeResponseModal: () => void;
}

export function useActionResponseModal(): UseActionResponseModalResult {
  const [responseModalState, setResponseModalState] = useState<{
    isOpen: boolean;
    response: ComponentActionResult | null;
  }>({
    isOpen: false,
    response: null,
  });

  const openResponseModal = (response: ComponentActionResult) => {
    setResponseModalState({ isOpen: true, response });
  };

  const closeResponseModal = () => {
    setResponseModalState({ isOpen: false, response: null });
  };

  return {
    responseModalState,
    openResponseModal,
    closeResponseModal,
  };
}

interface UseExecuteComponentActionOptions {
  onResponseReceived?: (response: ComponentActionResult) => void;
}

export function useExecuteComponentAction(
  options?: UseExecuteComponentActionOptions,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      deviceIp,
      componentKey,
      action,
      parameters,
    }: ExecuteComponentActionParams): Promise<ComponentActionResult> => {
      let cleanAction = action;
      if (!action.startsWith("Legacy.") && action.includes(".")) {
        cleanAction = action.split(".").pop() || action;
      }

      return deviceApi.executeComponentAction(
        deviceIp,
        componentKey,
        cleanAction,
        parameters,
      );
    },
    onSuccess: (result, variables) => {
      if (
        !GET_ACTIONS.some((getAction) => variables.action.includes(getAction))
      ) {
        queryClient.invalidateQueries({
          queryKey: ["device", "status", variables.deviceIp],
        });
      }

      options?.onResponseReceived?.(result);

      const shouldShowModal =
        shouldShowResponseData(variables.action) && hasResponseData(result);

      if (result.success) {
        if (!shouldShowModal) {
          toast.success(
            result.message ||
              `Action ${variables.action} executed successfully`,
          );
        }
      } else {
        toast.error(result.error || `Action ${variables.action} failed`);
      }
    },
    onError: (error, variables) => {
      toast.error(`Failed to execute ${variables.action}: ${error}`);
    },
  });
}

function formatActionName(action: string): string {
  const specialCases: Record<string, string> = {
    WiFi: "WiFi",
    AP: "AP",
    API: "API",
    HTTP: "HTTP",
    HTTPS: "HTTPS",
    URL: "URL",
    ID: "ID",
    UI: "UI",
    TLS: "TLS",
    CA: "CA",
    OTA: "OTA",
    KVS: "KVS",
    KNX: "KNX",
    WS: "WS",
    BLE: "BLE",
    MQTT: "MQTT",
  };

  return (
    action
      // Insert space before capital letters following lowercase letters
      .replace(/([a-z])([A-Z])/g, "$1 $2")
      // Handle consecutive capitals followed by lowercase (e.g., "HTTPRequest" → "HTTP Request")
      .replace(/([A-Z])([A-Z][a-z])/g, "$1 $2")
      // Split by spaces and handle special cases
      .split(" ")
      .map((word) => specialCases[word] || word)
      .join(" ")
      // Ensure first letter is capitalized
      .replace(/^./, (str) => str.toUpperCase())
  );
}

export function getActionDisplayName(
  action: string,
  componentKey?: string,
): string {
  if (action.startsWith("Legacy.")) {
    const legacyName = action.replace("Legacy.", "");
    return `Legacy ${formatActionName(legacyName)}`;
  }

  const parts = action.split(".");
  const cleanAction = parts[parts.length - 1];
  const actionPrefix = parts.length > 1 ? parts[0] : "";

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

    // Cover actions
    Open: "Open",
    Close: "Close",
    Stop: "Stop",
    GoToPosition: "Go to Position",

    // Zigbee actions
    StartNetworkSteering: "Start Pairing",
    ClearNetwork: "Clear Network",

    // Cloud actions
    Connect: "Connect",
    Disconnect: "Disconnect",

    // Common actions from the API
    GetStatus: "Get Status",
    GetConfig: "Get Config",
    SetConfig: "Set Config",
    SetAuth: "Set Auth",
    GetDeviceInfo: "Get Device Info",
    ListMethods: "List Methods",
    CheckForUpdate: "Check for Update",
    ResetWiFiConfig: "Reset WiFi Config",
    DetectLocation: "Detect Location",
    ListTimezones: "List Timezones",
    GetComponents: "Get Components",
    ListAPClients: "List AP Clients",
    CheckExpression: "Check Expression",
    DeleteAll: "Delete All",
    ListSupported: "List Supported",
    PutCode: "Put Code",
    GetCode: "Get Code",
    GetMany: "Get Many",
    PutTLSClientKey: "Put TLS Client Key",
    PutTLSClientCert: "Put TLS Client Cert",
    PutUserCA: "Put User CA",
    InstallAlt: "Install Alternative",
  };

  if (componentKey) {
    const key = componentKey.split(":")[0];
    if (!action.toLowerCase().includes(key.toLowerCase())) {
      return `${actionPrefix} ${formatActionName(cleanAction)}`;
    }
  }

  // Check custom mappings first, then fall back to automatic formatting
  return actionMap[cleanAction] || formatActionName(cleanAction);
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

export function isComingSoonAction(action: string): boolean {
  const cleanAction = action.includes(".")
    ? action.split(".").pop() || action
    : action;

  // Only disable specific actions that are not yet implemented
  // SetConfig is now enabled and fully implemented
  const comingSoonActions = [
    "SetAuth",
    "PutCode",
    "PutTLSClientKey",
    "PutTLSClientCert",
    "PutUserCA",
    "InstallAlt",
    "SetTime",
    "SetProfile",
    "Identify",
  ];

  return comingSoonActions.includes(cleanAction);
}

/**
 * Determines if an action response should display data to the user
 */
export function shouldShowResponseData(action: string): boolean {
  return GET_ACTIONS.some(
    (getAction) => action.includes(getAction) || action.endsWith(getAction),
  );
}

/**
 * Checks if a response contains meaningful data to display
 */
export function hasResponseData(response: ComponentActionResult): boolean {
  return !!(
    response.data &&
    typeof response.data === "object" &&
    Object.keys(response.data).length > 0
  );
}

function isMethodAvailable(
  availableMethods: string[],
  componentTypeFromAction: string,
): boolean {
  return availableMethods.some((method) => {
    const cleanMethod = method.toLowerCase();

    return (
      cleanMethod.startsWith(componentTypeFromAction + ".") ||
      cleanMethod === componentTypeFromAction
    );
  });
}

export function getComponentKeyForAction(
  action: string,
  component: {
    key: string;
    type: string;
    id: number | null;
    available_actions: string[];
  },
): string {
  if (action.startsWith("Legacy.")) {
    return component.key;
  }

  // Extract component type from action (e.g., "Switch.Toggle" -> "switch")
  const actionParts = action.split(".");
  if (actionParts.length < 2) {
    // If no dot, fallback to component.key
    return component.key;
  }

  const componentTypeFromAction = actionParts[0].toLowerCase();
  const availableMethods = component?.available_actions;

  // For components that need ID (switch, input, cover, etc.)
  let componentKey = componentTypeFromAction;
  if (component.id !== null && component.id !== undefined) {
    componentKey = `${componentTypeFromAction}:${component.id}`;
  }

  // If we have available methods, verify the key exists
  if (availableMethods) {
    const methodExists = isMethodAvailable(availableMethods, componentKey);
    if (methodExists) {
      return componentKey;
    }
  }

  // Fallback to original component.key
  return component.key;
}
