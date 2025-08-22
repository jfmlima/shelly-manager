export interface Device {
  ip: string;
  status: string;
  device_type: string;
  device_name: string;
  firmware_version: string;
  response_time: number | null;
  error_message?: string | null;
  last_seen?: string | null;
}

export interface Component {
  key: string;
  type: string;
  id: number | null;
  status: Record<string, unknown>;
  config: Record<string, unknown>;
  available_actions: string[];
}

export interface SwitchComponent extends Component {
  type: "switch";
  status: {
    output: boolean;
    apower: number;
    voltage: number;
    current: number;
    freq: number;
    temperature?: {
      tC: number;
      tF: number;
    };
    aenergy?: {
      total: number;
    };
  };
  config: {
    name?: string | null;
    auto_on: boolean;
    auto_off: boolean;
    power_limit: number;
    current_limit: number;
  };
}

export interface InputComponent extends Component {
  type: "input";
  status: {
    state: boolean;
  };
  config: {
    name?: string | null;
    type: string;
    enable: boolean;
    invert: boolean;
  };
}

export interface CoverComponent extends Component {
  type: "cover";
  status: {
    state: string;
    current_pos?: number;
    apower: number;
    voltage: number;
    temperature?: {
      tC: number;
      tF: number;
    };
    last_direction: string;
  };
  config: {
    name?: string | null;
    maxtime_open: number;
    maxtime_close: number;
    power_limit: number;
  };
}

export interface SystemComponent extends Component {
  type: "sys";
  status: {
    mac: string;
    restart_required: boolean;
    uptime: number;
    ram_size: number;
    ram_free: number;
    available_updates: Record<string, UpdateInfo>;
  };
  config: {
    device: {
      name?: string | null;
      fw_id: string;
    };
    location?: {
      tz: string;
    };
  };
}

export interface CloudComponent extends Component {
  type: "cloud";
  status: {
    connected: boolean;
  };
  config: {
    enable: boolean;
    server?: string;
  };
}

export interface ZigbeeComponent extends Component {
  type: "zigbee";
  status: {
    network_state: string;
  };
  config: Record<string, unknown>;
}

export interface BleComponent extends Component {
  type: "ble";
  status: Record<string, unknown>;
  config: {
    enable: boolean;
    rpc: {
      enable: boolean;
    };
  };
}

export interface UpdateInfo {
  version: string;
  build_id: string;
  name?: string;
  desc?: string;
}

export interface DeviceSummary {
  device_name: string | null;
  mac_address: string | null;
  firmware_version: string | null;
  uptime: number;
  cloud_connected: boolean;
  switch_count: number;
  input_count: number;
  cover_count: number;
  total_power: number;
  any_switch_on: boolean;
  has_updates: boolean;
  available_updates: Record<string, UpdateInfo>;
  restart_required: boolean;
  last_updated: string;
}

export interface FirmwareInfo {
  current_version: string | null;
  available_updates: Record<string, UpdateInfo>;
  restart_required: boolean;
}

export interface DeviceStatus {
  ip: string;
  components: Component[];
  summary: DeviceSummary;
  firmware: FirmwareInfo;
  last_updated: string;
  total_components: number;
  available_methods: string[];
}

export interface DeviceStatusError {
  ip: string;
  error: string;
}

export interface ActionResult {
  ip: string;
  success: boolean;
  message?: string;
  error?: string | null;
  action_type?: string;
}

export interface BulkActionResult {
  total: number;
  successful: number;
  failed: number;
  results: ActionResult[];
}

export interface BulkUpdateRequest {
  device_ips: string[];
  channel?: "stable" | "beta";
}

export interface ScanRequest {
  start_ip?: string;
  end_ip?: string;
  use_predefined?: boolean;
  timeout?: number;
  max_workers?: number;
}

export interface ComponentActionResult {
  ip: string;
  component_key: string;
  action: string;
  success: boolean;
  message?: string;
  error?: string;
  data?: string | Record<string, unknown>;
}

export interface BulkOperationRequest {
  device_ips: string[];
  operation: "update" | "reboot" | "factory_reset";
  channel?: string;
  [key: string]: unknown;
}

// Type guards for components
export type ComponentType =
  | SwitchComponent
  | InputComponent
  | CoverComponent
  | SystemComponent
  | CloudComponent
  | ZigbeeComponent
  | BleComponent;

export function isSwitchComponent(
  component: Component,
): component is SwitchComponent {
  return component.type === "switch";
}

export function isInputComponent(
  component: Component,
): component is InputComponent {
  return component.type === "input";
}

export function isCoverComponent(
  component: Component,
): component is CoverComponent {
  return component.type === "cover";
}

export function isSystemComponent(
  component: Component,
): component is SystemComponent {
  return component.type === "sys";
}

export function isCloudComponent(
  component: Component,
): component is CloudComponent {
  return component.type === "cloud";
}

export function isZigbeeComponent(
  component: Component,
): component is ZigbeeComponent {
  return component.type === "zigbee";
}

export function isBleComponent(
  component: Component,
): component is BleComponent {
  return component.type === "ble";
}
