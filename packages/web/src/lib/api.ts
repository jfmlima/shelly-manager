import axios from "axios";
import type {
  Device,
  DeviceStatus,
  ActionResult,
  ConfigResponse,
  BulkUpdateRequest,
  ConfigUpdateRequest,
  ScanRequest,
  ComponentActionResult,
} from "@/types/api";

const baseURL = import.meta.env.VITE_BASE_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${baseURL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

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
    const response = await apiClient.get("/devices/scan", { params });
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
    const response = await apiClient.post("/devices/bulk", {
      device_ips: deviceIps,
      operation,
      ...parameters,
    });
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

  getDeviceConfig: async (ip: string): Promise<ConfigResponse> => {
    const response = await apiClient.get(`/devices/${ip}/config`);
    return response.data;
  },

  updateDeviceConfig: async (
    ip: string,
    request: ConfigUpdateRequest,
  ): Promise<ConfigResponse> => {
    const response = await apiClient.post(`/devices/${ip}/config`, request);
    return response.data;
  },

  executeComponentAction: async (
    ip: string,
    componentKey: string,
    action: string,
    parameters: Record<string, unknown> = {},
  ): Promise<ComponentActionResult> => {
    const response = await apiClient.post(
      `/devices/${ip}/components/${componentKey}/actions/${action}`,
      { parameters },
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
