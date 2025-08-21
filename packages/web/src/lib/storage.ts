import type { Device, ScanRequest } from "@/types/api";

export const CACHE_VERSION = "1.0";
export const CACHE_KEY = "shelly-scan-results";
export const MAX_CACHE_AGE_MS = 2 * 24 * 60 * 60 * 1000; // 2 days

export interface ScanCache {
  devices: Device[];
  timestamp: string; // ISO string
  scanParams: ScanRequest;
  version: string;
  deviceCount: number;
}

class StorageManager {
  private isStorageAvailable(): boolean {
    try {
      const test = "__storage_test__";
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }

  private handleStorageError(error: Error, operation: string): void {
    console.error(`Storage ${operation} failed:`, error);
  }

  saveScanResults(devices: Device[], scanParams: ScanRequest): void {
    if (!this.isStorageAvailable()) {
      this.handleStorageError(new Error("Storage not available"), "save");
      return;
    }

    try {
      const cache: ScanCache = {
        devices,
        timestamp: new Date().toISOString(),
        scanParams,
        version: CACHE_VERSION,
        deviceCount: devices.length,
      };

      localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
    } catch (error) {
      this.handleStorageError(error as Error, "save");
    }
  }

  loadScanResults(): ScanCache | null {
    if (!this.isStorageAvailable()) {
      this.handleStorageError(new Error("Storage not available"), "load");
      return null;
    }

    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (!cached) {
        return null;
      }

      const parsed = JSON.parse(cached) as ScanCache;

      if (!this.validateCacheIntegrity(parsed)) {
        console.warn("Invalid cache structure, clearing cache");
        this.clearScanResults();
        return null;
      }

      return parsed;
    } catch (error) {
      this.handleStorageError(error as Error, "load");
      this.clearScanResults();
      return null;
    }
  }

  clearScanResults(): void {
    if (!this.isStorageAvailable()) {
      return;
    }

    try {
      localStorage.removeItem(CACHE_KEY);
    } catch (error) {
      this.handleStorageError(error as Error, "clear");
    }
  }

  isDataStale(thresholdMs: number = MAX_CACHE_AGE_MS): boolean {
    const cache = this.loadScanResults();
    if (!cache) {
      return false;
    }

    const cacheDate = new Date(cache.timestamp);
    const now = new Date();
    return now.getTime() - cacheDate.getTime() > thresholdMs;
  }

  private validateCacheIntegrity(cache: unknown): cache is ScanCache {
    if (!cache || typeof cache !== "object") {
      return false;
    }

    const c = cache as Record<string, unknown>;

    return (
      typeof c.version === "string" &&
      c.version === CACHE_VERSION &&
      typeof c.timestamp === "string" &&
      Array.isArray(c.devices) &&
      typeof c.scanParams === "object" &&
      c.scanParams !== null &&
      typeof c.deviceCount === "number"
    );
  }

  getLastScanTimestamp(): Date | null {
    const cache = this.loadScanResults();
    return cache ? new Date(cache.timestamp) : null;
  }

  getCachedDeviceCount(): number {
    const cache = this.loadScanResults();
    return cache ? cache.deviceCount : 0;
  }
}

export const storageManager = new StorageManager();

export const saveScanResults = (devices: Device[], scanParams: ScanRequest) =>
  storageManager.saveScanResults(devices, scanParams);

export const loadScanResults = () => storageManager.loadScanResults();

export const clearScanResults = () => storageManager.clearScanResults();

export const isDataStale = (thresholdMs?: number) =>
  storageManager.isDataStale(thresholdMs);

export const getLastScanTimestamp = () => storageManager.getLastScanTimestamp();

export const getCachedDeviceCount = () => storageManager.getCachedDeviceCount();
