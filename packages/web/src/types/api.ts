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

export interface EthernetComponent extends Component {
  type: "eth";
  status: {
    ip?: string;
    ip6?: string[];
  };
  config: {
    enable: boolean;
    server_mode: boolean;
    ipv4mode: string;
    netmask?: string;
    gw?: string;
    nameserver?: string;
  };
}

export interface BluetoothHomeComponent extends Component {
  type: "bthome";
  status: {
    errors?: string[];
  };
  config: {
    enable: boolean;
  };
}

export interface KnxComponent extends Component {
  type: "knx";
  status: Record<string, unknown>;
  config: {
    enable: boolean;
    ia?: string;
    routing?: {
      addr: string;
    };
  };
}

export interface MqttComponent extends Component {
  type: "mqtt";
  status: {
    connected: boolean;
  };
  config: {
    enable: boolean;
    server?: string;
    client_id?: string;
    user?: string;
    topic_prefix?: string;
    rpc_ntf: boolean;
    status_ntf: boolean;
    use_client_cert: boolean;
    enable_rpc: boolean;
    enable_control: boolean;
  };
}

export interface WifiComponent extends Component {
  type: "wifi";
  status: {
    sta_ip?: string;
    sta_ip6?: string[];
    status: string;
    ssid?: string;
    bssid?: string;
    rssi: number;
  };
  config: Record<string, unknown>;
}

export interface WebSocketComponent extends Component {
  type: "ws";
  status: {
    connected: boolean;
  };
  config: Record<string, unknown>;
}

export interface EMComponent extends Component {
  type: "em";
  status: {
    a_current?: number;
    a_voltage?: number;
    a_act_power?: number;
    a_aprt_power?: number;
    a_pf?: number;
    a_freq?: number;
    b_current?: number;
    b_voltage?: number;
    b_act_power?: number;
    b_aprt_power?: number;
    b_pf?: number;
    b_freq?: number;
    c_current?: number;
    c_voltage?: number;
    c_act_power?: number;
    c_aprt_power?: number;
    c_pf?: number;
    c_freq?: number;
    n_current?: number;
    total_current?: number;
    total_act_power?: number;
    total_aprt_power?: number;
  };
  config: {
    name?: string | null;
    ct_type?: string;
  };
}

export interface EM1Component extends Component {
  type: "em1";
  status: {
    current?: number;
    voltage?: number;
    act_power?: number;
    aprt_power?: number;
    pf?: number;
    freq?: number;
  };
  config: {
    name?: string | null;
    ct_type?: string;
    reverse?: boolean;
  };
}

export interface EMDataComponent extends Component {
  type: "emdata";
  status: {
    a_total_act_energy?: number;
    a_total_act_ret_energy?: number;
    b_total_act_energy?: number;
    b_total_act_ret_energy?: number;
    c_total_act_energy?: number;
    c_total_act_ret_energy?: number;
    total_act?: number;
    total_act_ret?: number;
  };
  config: Record<string, unknown>;
}

export interface EM1DataComponent extends Component {
  type: "em1data";
  status: {
    total_act_energy?: number;
    total_act_ret_energy?: number;
  };
  config: Record<string, unknown>;
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
  targets: string[];
  use_mdns?: boolean;
  timeout?: number;
  max_workers?: number;
}

export interface Credential {
  mac: string;
  username: string;
  last_seen_ip?: string;
  last_used?: string;
}

export interface CredentialCreateRequest {
  mac: string;
  username?: string;
  password: string;
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
  | BleComponent
  | EthernetComponent
  | BluetoothHomeComponent
  | KnxComponent
  | MqttComponent
  | WifiComponent
  | WebSocketComponent
  | EMComponent
  | EM1Component
  | EMDataComponent
  | EM1DataComponent;

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

export function isEthernetComponent(
  component: Component,
): component is EthernetComponent {
  return component.type === "eth";
}

export function isBluetoothHomeComponent(
  component: Component,
): component is BluetoothHomeComponent {
  return component.type === "bthome";
}

export function isKnxComponent(
  component: Component,
): component is KnxComponent {
  return component.type === "knx";
}

export function isMqttComponent(
  component: Component,
): component is MqttComponent {
  return component.type === "mqtt";
}

export function isWifiComponent(
  component: Component,
): component is WifiComponent {
  return component.type === "wifi";
}

export function isWebSocketComponent(
  component: Component,
): component is WebSocketComponent {
  return component.type === "ws";
}

export function isEMComponent(component: Component): component is EMComponent {
  return component.type === "em";
}

export function isEM1Component(
  component: Component,
): component is EM1Component {
  return component.type === "em1";
}

export function isEMDataComponent(
  component: Component,
): component is EMDataComponent {
  return component.type === "emdata";
}

export function isEM1DataComponent(
  component: Component,
): component is EM1DataComponent {
  return component.type === "em1data";
}
