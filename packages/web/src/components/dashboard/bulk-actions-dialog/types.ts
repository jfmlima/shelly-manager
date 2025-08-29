import type { Device, ActionResult } from "@/types/api";

export type BulkActionType =
  | "update"
  | "reboot"
  | "factory_reset"
  | "export_config"
  | "apply_config";

export interface BulkProgress {
  total: number;
  completed: number;
  failed: number;
  results: ActionResult[];
  isRunning: boolean;
  // Timing fields for dynamic progress
  startTime?: number;
  estimatedDurationMs?: number;
  currentProgress?: number;
  timeElapsedMs?: number;
  estimatedTimeRemainingMs?: number;
}

export interface BulkActionsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedDevices: Device[];
  onComplete?: () => void;
}

export interface ActionSelectionProps {
  onActionSelect: (action: BulkActionType) => void;
}

export interface ActionConfigurationProps {
  selectedAction: BulkActionType;
  updateChannel: "stable" | "beta";
  onUpdateChannelChange: (channel: "stable" | "beta") => void;
  confirmFactoryReset: boolean;
  onConfirmFactoryResetChange: (confirm: boolean) => void;
  selectedComponentTypes: string[];
  onSelectedComponentTypesChange: (types: string[]) => void;
  selectedComponentType: string;
  onSelectedComponentTypeChange: (type: string) => void;
  configurationJson: string;
  onConfigurationJsonChange: (json: string) => void;
  configError: string;
  onExecute: () => void;
  onCancel: () => void;
}

export interface ProgressDisplayProps {
  progress: BulkProgress;
  showDetails: boolean;
  onShowDetailsChange: (show: boolean) => void;
  onClose: () => void;
  onReset: () => void;
}

export interface DevicePreviewProps {
  selectedDevices: Device[];
}

export const CONFIGURABLE_COMPONENT_TYPES = [
  "switch",
  "input",
  "cover",
  "sys",
  "cloud",
  "wifi",
  "ble",
  "mqtt",
  "ws",
  "script",
  "knx",
  "modbus",
  "zigbee",
] as const;

export const BULK_ACTION_STYLES = {
  actionCard: "transition-shadow cursor-pointer hover:shadow-md",
  dangerCard: "border-destructive/20 hover:border-destructive/40",
  disabledCard: "opacity-60 cursor-not-allowed",
  progressGrid: "grid grid-cols-3 gap-4 text-center",
  componentGrid: "grid grid-cols-2 md:grid-cols-3 gap-2",
  warningBox: "p-4 bg-destructive/5 border border-destructive/20 rounded-lg",
  infoBox: "p-4 bg-blue-50 border border-blue-200 rounded-lg",
  safetyBox: "p-4 bg-orange-50 border border-orange-200 rounded-lg",
} as const;

export interface ActionCardData {
  id: BulkActionType;
  titleKey: string;
  descriptionKey: string;
  icon: React.ReactNode;
  isComingSoon?: boolean;
}

// Base props for all action configuration components
export interface BaseActionConfigProps {
  onExecute: () => void;
  onCancel: () => void;
}

// Specific action configuration props
export interface UpdateActionConfigProps extends BaseActionConfigProps {
  updateChannel: "stable" | "beta";
  onUpdateChannelChange: (channel: "stable" | "beta") => void;
}

export interface FactoryResetConfigProps extends BaseActionConfigProps {
  confirmFactoryReset: boolean;
  onConfirmFactoryResetChange: (confirm: boolean) => void;
}

export interface ExportConfigActionProps extends BaseActionConfigProps {
  selectedComponentTypes: string[];
  onSelectedComponentTypesChange: (types: string[]) => void;
}

export interface ApplyConfigActionProps extends BaseActionConfigProps {
  selectedComponentType: string;
  onSelectedComponentTypeChange: (type: string) => void;
  configurationJson: string;
  onConfigurationJsonChange: (json: string) => void;
  configError: string;
}
