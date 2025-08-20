import type { ComponentActionResult } from "@/types/api";

export type ResponseDisplayType = "modal" | "inline" | "none";

/**
 * Determines if an action response should display data to the user
 */
export function shouldShowResponseData(action: string): boolean {
  const getActions = [
    "GetStatus",
    "GetConfig",
    "GetInfo",
    "GetDeviceInfo",
    "GetComponents",
    "ListMethods",
    "CheckForUpdate",
    "GetCustomMethods",
  ];

  return getActions.some(
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

/**
 * Formats action names for display
 */
export function formatActionDisplayName(action: string): string {
  const cleanAction = action.includes(".")
    ? action.split(".").pop() || action
    : action;

  return cleanAction
    .replace(/([A-Z])/g, " $1")
    .trim()
    .split(" ")
    .map((word, index) =>
      index === 0
        ? word.charAt(0).toUpperCase() + word.slice(1)
        : word.toLowerCase(),
    )
    .join(" ");
}

/**
 * Gets a user-friendly description for common actions
 */
export function getActionDescription(action: string): string {
  const descriptions: Record<string, string> = {
    GetStatus: "Retrieve current status and readings",
    GetConfig: "Get current configuration settings",
    GetInfo: "Get device information",
    GetDeviceInfo: "Get detailed device information",
    GetComponents: "List all available components",
    ListMethods: "List all available RPC methods",
    CheckForUpdate: "Check for firmware updates",
    Toggle: "Switch the current state",
    Set: "Set a specific value",
    Reboot: "Restart the device",
    Update: "Update firmware",
    FactoryReset: "Reset to factory defaults",
    ResetCounters: "Reset energy counters",
    Open: "Open the cover",
    Close: "Close the cover",
    Stop: "Stop current movement",
    GoToPosition: "Move to specific position",
    Connect: "Connect to cloud service",
    Disconnect: "Disconnect from cloud service",
    StartNetworkSteering: "Start device pairing mode",
    ClearNetwork: "Clear network settings",
  };

  const cleanAction = action.includes(".")
    ? action.split(".").pop() || action
    : action;

  return (
    descriptions[cleanAction] ||
    `Execute ${formatActionDisplayName(cleanAction)}`
  );
}

/**
 * Determines the icon to use for an action type
 */
export function getActionResponseIcon(action: string): string {
  const iconMap: Record<string, string> = {
    GetStatus: "Info",
    GetConfig: "Settings",
    GetInfo: "Info",
    GetDeviceInfo: "Info",
    GetComponents: "List",
    ListMethods: "List",
    CheckForUpdate: "Download",
    Toggle: "ToggleLeft",
    Set: "Settings",
    Reboot: "Power",
    Update: "Download",
    FactoryReset: "AlertTriangle",
    ResetCounters: "RotateCcw",
    Open: "ChevronUp",
    Close: "ChevronDown",
    Stop: "Square",
    GoToPosition: "Target",
    Connect: "Wifi",
    Disconnect: "WifiOff",
    StartNetworkSteering: "Radio",
    ClearNetwork: "Trash2",
  };

  const cleanAction = action.includes(".")
    ? action.split(".").pop() || action
    : action;

  return iconMap[cleanAction] || "Play";
}

/**
 * Checks if an action is a query/read operation (vs a command/write operation)
 */
export function isQueryAction(action: string): boolean {
  const queryActions = [
    "Get",
    "List",
    "Check",
    "Status",
    "Info",
    "Config",
    "Components",
    "Methods",
  ];

  return queryActions.some((queryType) => action.includes(queryType));
}

/**
 * Checks if an action is destructive and needs confirmation
 */
export function isDestructiveAction(action: string): boolean {
  const destructiveActions = [
    "FactoryReset",
    "Reset",
    "Delete",
    "Clear",
    "Reboot",
    "Update",
  ];

  return destructiveActions.some((destructiveType) =>
    action.includes(destructiveType),
  );
}

/**
 * Extracts the correct component key from an action name and component info
 * @param action - Action name like "Switch.Toggle" or "Sys.Reboot"
 * @param component - Component object with key, type, and id
 * @param availableMethods - Optional list of available methods from device status
 * @returns The correct component key to use for the API call
 */
export function getComponentKeyForAction(
  action: string,
  component: {
    key: string;
    type: string;
    id: number | null;
    available_actions: string[];
  },
): string {
  // Extract component type from action (e.g., "Switch.Toggle" -> "switch")
  const actionParts = action.split(".");
  if (actionParts.length < 2) {
    // If no dot, fallback to component.key
    return component.key;
  }

  const componentTypeFromAction = actionParts[0];
  const availableMethods = component?.available_actions;

  // For components that need ID (switch, input, cover, etc.)
  if (component.id !== null && component.id !== undefined) {
    const keyWithId = `${componentTypeFromAction}:${component.id}`;

    // If we have available methods, verify the key exists
    if (availableMethods) {
      const methodExists = availableMethods.some(
        (method) => method.startsWith(keyWithId + ".") || method === keyWithId,
      );
      if (methodExists) {
        return keyWithId;
      }
    }

    return keyWithId;
  }

  // For components without ID (sys, cloud, zigbee, etc.)
  if (availableMethods) {
    const methodExists = availableMethods.some(
      (method) =>
        method.startsWith(componentTypeFromAction + ".") ||
        method === componentTypeFromAction,
    );
    if (methodExists) {
      return componentTypeFromAction;
    }
  }

  // Fallback to original component.key
  return component.key;
}
