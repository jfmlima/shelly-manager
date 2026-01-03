import axios from "axios";
import type {
  Device,
  DeviceStatus,
  ActionResult,
  BulkUpdateRequest,
  ScanRequest,
  ComponentActionResult,
} from "@/types/api";
import { loadAppSettings } from "./settings";

declare global {
  interface Window {
    _env_?: {
      VITE_BASE_API_URL?: string;
    };
  }
}

const getApiBaseUrl = (): string => {
  const savedApiUrl = localStorage.getItem("shelly-manager-api-url");

  const runtimeApiUrl = window._env_?.VITE_BASE_API_URL;
  const buildTimeApiUrl = import.meta.env.VITE_BASE_API_URL;

  return (
    savedApiUrl || runtimeApiUrl || buildTimeApiUrl || "http://localhost:8000"
  );
};

const baseURL = getApiBaseUrl();

export const getBulkOperationTimeout = (deviceCount: number): number => {
  const baseTimeout = 30000;
  const perDeviceTimeout = 5000;
  const maxTimeout = 300000;

  return Math.min(baseTimeout + deviceCount * perDeviceTimeout, maxTimeout);
};

export const apiClient = axios.create({
  baseURL: `${baseURL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
  paramsSerializer: (params) => {
    const searchParams = new URLSearchParams();
    for (const key in params) {
      const val = params[key];
      if (Array.isArray(val)) {
        val.forEach((v) => searchParams.append(key, v));
      } else if (val !== undefined && val !== null) {
        searchParams.append(key, val.toString());
      }
    }
    return searchParams.toString();
  },
});

export const updateApiBaseUrl = () => {
  const newBaseUrl = getApiBaseUrl();
  apiClient.defaults.baseURL = `${newBaseUrl}/api`;
};

export const validateApiUrl = (
  url: string,
): { valid: boolean; error?: string } => {
  if (!url || typeof url !== "string") {
    return { valid: false, error: "URL is required" };
  }

  const cleanUrl = url.replace(/\/+$/, "");

  try {
    const parsedUrl = new URL(cleanUrl);

    if (!["http:", "https:"].includes(parsedUrl.protocol)) {
      return { valid: false, error: "URL must use HTTP or HTTPS protocol" };
    }

    if (!parsedUrl.hostname) {
      return { valid: false, error: "URL must have a valid hostname" };
    }

    if (parsedUrl.pathname && parsedUrl.pathname !== "/") {
      return {
        valid: false,
        error:
          "API URL should not include a path (e.g., use http://host:8000, not http://host:8000/api)",
      };
    }

    return { valid: true };
  } catch (error) {
    return {
      valid: false,
      error: error instanceof Error ? error.message : "Invalid URL format",
    };
  }
};

apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error("API Request Error:", error);
    return Promise.reject(error);
  },
);

apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error("API Response Error:", error.response?.data || error.message);
    return Promise.reject(error);
  },
);

export const deviceApi = {
  scanDevices: async (params: ScanRequest): Promise<Device[]> => {
    const settings = loadAppSettings();
    const response = await apiClient.get("/devices/scan", {
      params,
      // Use configured timeout for the overall request
      timeout: settings.scanRequestTimeout,
    });
    return response.data;
  },

  getDeviceStatus: async (
    ip: string,
    includeUpdates = true,
  ): Promise<DeviceStatus> => {
    const response = await apiClient.get(`/devices/${ip}/status`, {
      params: { include_updates: includeUpdates },
    });
    return response.data;
  },

  updateDevice: async (
    ip: string,
    channel: "stable" | "beta" = "stable",
  ): Promise<ActionResult> => {
    const response = await apiClient.post(`/devices/${ip}/update`, { channel });
    return response.data;
  },

  bulkExecuteOperation: async (
    deviceIps: string[],
    operation: "update" | "reboot" | "factory_reset",
    parameters: Record<string, unknown> = {},
  ): Promise<ActionResult[]> => {
    const timeout = getBulkOperationTimeout(deviceIps.length);
    const response = await apiClient.post(
      "/devices/bulk",
      {
        device_ips: deviceIps,
        operation,
        ...parameters,
      },
      { timeout },
    );
    return response.data;
  },

  bulkUpdateDevices: async (
    request: BulkUpdateRequest,
  ): Promise<ActionResult[]> => {
    return deviceApi.bulkExecuteOperation(request.device_ips, "update", {
      channel: request.channel || "stable",
    });
  },

  rebootDevice: async (ip: string): Promise<ActionResult> => {
    const response = await apiClient.post(`/devices/${ip}/reboot`);
    return response.data;
  },

  factoryResetDevice: async (ip: string): Promise<ActionResult> => {
    const results = await deviceApi.bulkExecuteOperation([ip], "factory_reset");
    return results[0];
  },

  executeComponentAction: async (
    ip: string,
    componentKey: string,
    action: string,
    parameters: Record<string, unknown> = {},
  ): Promise<ComponentActionResult> => {
    const response = await apiClient.post(
      `/devices/${ip}/components/${componentKey}/actions/${action}`,
      parameters,
    );
    return response.data;
  },

  bulkExportConfig: async (
    deviceIps: string[],
    componentTypes: string[],
  ): Promise<Record<string, unknown>> => {
    const timeout = getBulkOperationTimeout(deviceIps.length);
    const response = await apiClient.post(
      "/devices/bulk/config/export",
      {
        device_ips: deviceIps,
        component_types: componentTypes,
      },
      { timeout },
    );
    return response.data;
  },

  bulkApplyConfig: async (
    deviceIps: string[],
    componentType: string,
    config: Record<string, unknown>,
  ): Promise<ActionResult[]> => {
    const timeout = getBulkOperationTimeout(deviceIps.length);
    const response = await apiClient.post(
      "/devices/bulk/config/apply",
      {
        device_ips: deviceIps,
        component_type: componentType,
        config: config,
      },
      { timeout },
    );
    return response.data;
  },
};

export const handleApiError = (error: unknown): string => {
  if (typeof error === "object" && error !== null) {
    const errorObj = error as Record<string, unknown>;

    if (
      errorObj.response &&
      typeof errorObj.response === "object" &&
      errorObj.response !== null
    ) {
      const response = errorObj.response as Record<string, unknown>;
      if (
        response.data &&
        typeof response.data === "object" &&
        response.data !== null
      ) {
        const data = response.data as Record<string, unknown>;
        if (typeof data.error === "string") {
          return data.error;
        }
        if (typeof data.message === "string") {
          return data.message;
        }
      }
    }

    if (typeof errorObj.message === "string") {
      return errorObj.message;
    }
  }

  return "An unexpected error occurred";
};
