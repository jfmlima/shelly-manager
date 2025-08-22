/**
 * Configuration validation utilities for component configurations
 */

function hasProperty(obj: unknown, property: string): boolean {
  return typeof obj === "object" && obj !== null && property in obj;
}

function getProperty<T = unknown>(
  obj: unknown,
  property: string,
): T | undefined {
  if (hasProperty(obj, property)) {
    return (obj as Record<string, T>)[property];
  }
  return undefined;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

/**
 * Validates a configuration object for a specific component type
 */
export function validateComponentConfig(
  config: unknown,
  componentType: string,
): ValidationResult {
  const result: ValidationResult = {
    isValid: true,
    errors: [],
    warnings: [],
  };

  if (config === null || config === undefined) {
    result.errors.push("Configuration cannot be empty");
    result.isValid = false;
    return result;
  }

  if (typeof config !== "object" || Array.isArray(config)) {
    result.errors.push("Configuration must be a valid JSON object");
    result.isValid = false;
    return result;
  }

  const configRecord = config as Record<string, unknown>;
  switch (componentType) {
    case "switch":
      validateSwitchConfig(configRecord, result);
      break;
    case "input":
      validateInputConfig(configRecord, result);
      break;
    case "cover":
      validateCoverConfig(configRecord, result);
      break;
    case "sys":
      validateSystemConfig(configRecord, result);
      break;
    case "cloud":
      validateCloudConfig(configRecord, result);
      break;
    case "wifi":
      validateWifiConfig(configRecord, result);
      break;
    case "ble":
      validateBleConfig(configRecord, result);
      break;
    default:
      validateGenericConfig(configRecord, result);
  }

  return result;
}

function validateSwitchConfig(
  config: Record<string, unknown>,
  result: ValidationResult,
) {
  const output = getProperty<boolean>(config, "output");
  if (hasProperty(config, "output") && typeof output !== "boolean") {
    result.errors.push("'output' must be true or false");
  }

  const enable = getProperty<boolean>(config, "enable");
  if (hasProperty(config, "enable") && typeof enable !== "boolean") {
    result.errors.push("'enable' must be true or false");
  }

  const autoOn = getProperty<boolean>(config, "auto_on");
  if (hasProperty(config, "auto_on") && typeof autoOn !== "boolean") {
    result.errors.push("'auto_on' must be true or false");
  }

  const autoOff = getProperty<boolean>(config, "auto_off");
  if (hasProperty(config, "auto_off") && typeof autoOff !== "boolean") {
    result.errors.push("'auto_off' must be true or false");
  }

  const name = getProperty<string | null>(config, "name");
  if (
    hasProperty(config, "name") &&
    name !== null &&
    typeof name !== "string"
  ) {
    result.errors.push("'name' must be a string or null");
  }

  const inMode = getProperty<string>(config, "in_mode");
  if (hasProperty(config, "in_mode")) {
    const validModes = ["momentary", "follow", "flip", "detached"];
    if (!validModes.includes(inMode as string)) {
      result.errors.push(`'in_mode' must be one of: ${validModes.join(", ")}`);
    }
  }

  const initialState = getProperty<string>(config, "initial_state");
  if (hasProperty(config, "initial_state")) {
    const validStates = ["off", "on", "restore_last", "match_input"];
    if (!validStates.includes(initialState as string)) {
      result.errors.push(
        `'initial_state' must be one of: ${validStates.join(", ")}`,
      );
    }
  }

  const autoOnDelay = getProperty<number>(config, "auto_on_delay");
  if (hasProperty(config, "auto_on_delay") && typeof autoOnDelay !== "number") {
    result.errors.push("'auto_on_delay' must be a number");
  }

  const autoOffDelay = getProperty<number>(config, "auto_off_delay");
  if (
    hasProperty(config, "auto_off_delay") &&
    typeof autoOffDelay !== "number"
  ) {
    result.errors.push("'auto_off_delay' must be a number");
  }

  const powerLimit = getProperty<number>(config, "power_limit");
  if (hasProperty(config, "power_limit") && typeof powerLimit !== "number") {
    result.errors.push("'power_limit' must be a number");
  }

  const currentLimit = getProperty<number>(config, "current_limit");
  if (
    hasProperty(config, "current_limit") &&
    typeof currentLimit !== "number"
  ) {
    result.errors.push("'current_limit' must be a number");
  }

  const voltageLimit = getProperty<number>(config, "voltage_limit");
  if (
    hasProperty(config, "voltage_limit") &&
    typeof voltageLimit !== "number"
  ) {
    result.errors.push("'voltage_limit' must be a number");
  }
}

function validateInputConfig(
  config: Record<string, unknown>,
  result: ValidationResult,
) {
  const enable = getProperty<boolean>(config, "enable");
  if (hasProperty(config, "enable") && typeof enable !== "boolean") {
    result.errors.push("'enable' must be true or false");
  }

  const invert = getProperty<boolean>(config, "invert");
  if (hasProperty(config, "invert") && typeof invert !== "boolean") {
    result.errors.push("'invert' must be true or false");
  }

  const factoryReset = getProperty<boolean>(config, "factory_reset");
  if (
    hasProperty(config, "factory_reset") &&
    typeof factoryReset !== "boolean"
  ) {
    result.errors.push("'factory_reset' must be true or false");
  }

  const name = getProperty<string | null>(config, "name");
  if (
    hasProperty(config, "name") &&
    name !== null &&
    typeof name !== "string"
  ) {
    result.errors.push("'name' must be a string or null");
  }

  const type = getProperty<string>(config, "type");
  if (hasProperty(config, "type")) {
    const validTypes = ["switch", "button"];
    if (!validTypes.includes(type as string)) {
      result.errors.push(`'type' must be one of: ${validTypes.join(", ")}`);
    }
  }
}

function validateCoverConfig(
  config: Record<string, unknown>,
  result: ValidationResult,
) {
  const enable = getProperty<boolean>(config, "enable");
  if (hasProperty(config, "enable") && typeof enable !== "boolean") {
    result.errors.push("'enable' must be true or false");
  }

  const name = getProperty<string | null>(config, "name");
  if (
    hasProperty(config, "name") &&
    name !== null &&
    typeof name !== "string"
  ) {
    result.errors.push("'name' must be a string or null");
  }

  const motor = getProperty<Record<string, unknown>>(config, "motor");
  if (hasProperty(config, "motor") && motor) {
    const idlePowerThr = getProperty<number>(motor, "idle_power_thr");
    if (
      hasProperty(motor, "idle_power_thr") &&
      typeof idlePowerThr !== "number"
    ) {
      result.errors.push("'motor.idle_power_thr' must be a number");
    }
  }

  const positioning = getProperty<boolean>(config, "positioning");
  if (hasProperty(config, "positioning") && typeof positioning !== "boolean") {
    result.errors.push("'positioning' must be true or false");
  }
}

function validateSystemConfig(
  config: Record<string, unknown>,
  result: ValidationResult,
) {
  const device = getProperty<Record<string, unknown>>(config, "device");
  if (hasProperty(config, "device") && device) {
    const deviceName = getProperty<string | null>(device, "name");
    if (
      hasProperty(device, "name") &&
      deviceName !== null &&
      typeof deviceName !== "string"
    ) {
      result.errors.push("'device.name' must be a string or null");
    }

    const ecoMode = getProperty<boolean>(device, "eco_mode");
    if (hasProperty(device, "eco_mode") && typeof ecoMode !== "boolean") {
      result.errors.push("'device.eco_mode' must be true or false");
    }

    const discoverable = getProperty<boolean>(device, "discoverable");
    if (
      hasProperty(device, "discoverable") &&
      typeof discoverable !== "boolean"
    ) {
      result.errors.push("'device.discoverable' must be true or false");
    }
  }

  const location = getProperty<Record<string, unknown>>(config, "location");
  if (hasProperty(config, "location") && location) {
    const lat = getProperty<number>(location, "lat");
    if (hasProperty(location, "lat") && typeof lat !== "number") {
      result.errors.push("'location.lat' must be a number");
    }

    const lon = getProperty<number>(location, "lon");
    if (hasProperty(location, "lon") && typeof lon !== "number") {
      result.errors.push("'location.lon' must be a number");
    }

    const tz = getProperty<string>(location, "tz");
    if (hasProperty(location, "tz") && typeof tz !== "string") {
      result.errors.push("'location.tz' must be a string");
    }
  }
}

function validateCloudConfig(
  config: Record<string, unknown>,
  result: ValidationResult,
) {
  const enable = getProperty<boolean>(config, "enable");
  if (hasProperty(config, "enable") && typeof enable !== "boolean") {
    result.errors.push("'enable' must be true or false");
  }

  const server = getProperty<string>(config, "server");
  if (hasProperty(config, "server") && typeof server !== "string") {
    result.errors.push("'server' must be a string");
  }
}

function validateWifiConfig(
  config: Record<string, unknown>,
  result: ValidationResult,
) {
  const ap = getProperty<Record<string, unknown>>(config, "ap");
  if (hasProperty(config, "ap") && ap) {
    const apEnable = getProperty<boolean>(ap, "enable");
    if (hasProperty(ap, "enable") && typeof apEnable !== "boolean") {
      result.errors.push("'ap.enable' must be true or false");
    }

    const apSsid = getProperty<string>(ap, "ssid");
    if (hasProperty(ap, "ssid") && typeof apSsid !== "string") {
      result.errors.push("'ap.ssid' must be a string");
    }
  }

  const sta = getProperty<Record<string, unknown>>(config, "sta");
  if (hasProperty(config, "sta") && sta) {
    const staEnable = getProperty<boolean>(sta, "enable");
    if (hasProperty(sta, "enable") && typeof staEnable !== "boolean") {
      result.errors.push("'sta.enable' must be true or false");
    }

    const staSsid = getProperty<string>(sta, "ssid");
    if (hasProperty(sta, "ssid") && typeof staSsid !== "string") {
      result.errors.push("'sta.ssid' must be a string");
    }
  }
}

function validateBleConfig(
  config: Record<string, unknown>,
  result: ValidationResult,
) {
  const enable = getProperty<boolean>(config, "enable");
  if (hasProperty(config, "enable") && typeof enable !== "boolean") {
    result.errors.push("'enable' must be true or false");
  }

  const rpc = getProperty<Record<string, unknown>>(config, "rpc");
  if (hasProperty(config, "rpc") && rpc) {
    const rpcEnable = getProperty<boolean>(rpc, "enable");
    if (hasProperty(rpc, "enable") && typeof rpcEnable !== "boolean") {
      result.errors.push("'rpc.enable' must be true or false");
    }
  }
}

function validateGenericConfig(
  config: Record<string, unknown>,
  result: ValidationResult,
) {
  const enable = getProperty<boolean>(config, "enable");
  if (hasProperty(config, "enable") && typeof enable !== "boolean") {
    result.warnings.push("'enable' is typically a boolean field");
  }

  const name = getProperty<string | null>(config, "name");
  if (
    hasProperty(config, "name") &&
    name !== null &&
    typeof name !== "string"
  ) {
    result.warnings.push("'name' is typically a string or null");
  }
}

/**
 * Get validation examples for a specific component type
 */
export function getComponentConfigExamples(
  componentType: string,
): Array<{ description: string; value: string }> {
  const baseExamples = [
    { description: "Enable component", value: '{"enable": true}' },
    { description: "Disable component", value: '{"enable": false}' },
    { description: "Set display name", value: '{"name": "My Component"}' },
  ];

  switch (componentType) {
    case "switch":
      return [
        ...baseExamples,
        { description: "Turn switch on", value: '{"output": true}' },
        {
          description: "Set auto-off after 60s",
          value: '{"auto_off": true, "auto_off_delay": 60}',
        },
        { description: "Set input mode to flip", value: '{"in_mode": "flip"}' },
        {
          description: "Set initial state to restore last",
          value: '{"initial_state": "restore_last"}',
        },
      ];

    case "input":
      return [
        ...baseExamples,
        { description: "Set as button type", value: '{"type": "button"}' },
        { description: "Invert input logic", value: '{"invert": true}' },
        {
          description: "Enable factory reset",
          value: '{"factory_reset": true}',
        },
      ];

    case "cover":
      return [
        ...baseExamples,
        { description: "Enable positioning", value: '{"positioning": true}' },
        {
          description: "Set motor power threshold",
          value: '{"motor": {"idle_power_thr": 2.0}}',
        },
      ];

    case "sys":
      return [
        {
          description: "Set device name",
          value: '{"device": {"name": "Living Room Device"}}',
        },
        {
          description: "Enable eco mode",
          value: '{"device": {"eco_mode": true}}',
        },
        {
          description: "Set location",
          value:
            '{"location": {"lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"}}',
        },
        {
          description: "Hide from discovery",
          value: '{"device": {"discoverable": false}}',
        },
      ];

    case "cloud":
      return [
        { description: "Enable cloud connection", value: '{"enable": true}' },
        { description: "Disable cloud connection", value: '{"enable": false}' },
        {
          description: "Set custom server",
          value: '{"server": "custom.shelly.cloud:6012/jrpc"}',
        },
      ];

    case "ble":
      return [
        { description: "Enable Bluetooth", value: '{"enable": true}' },
        {
          description: "Enable RPC over BLE",
          value: '{"rpc": {"enable": true}}',
        },
        { description: "Disable Bluetooth", value: '{"enable": false}' },
      ];

    default:
      return baseExamples;
  }
}
