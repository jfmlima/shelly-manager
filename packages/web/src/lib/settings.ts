export interface AppSettings {
  tablePageSize: number;
  tableDensity: "compact" | "normal" | "comfortable";
  scanRequestTimeout: number; // in milliseconds
}

export const DEFAULT_SETTINGS: AppSettings = {
  tablePageSize: 10,
  tableDensity: "normal",
  scanRequestTimeout: 600000, // 10 minutes default
};

const STORAGE_KEY = "shelly-manager-settings";

export const loadAppSettings = (): AppSettings => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return DEFAULT_SETTINGS;

    const parsed = JSON.parse(saved);
    return { ...DEFAULT_SETTINGS, ...parsed };
  } catch (error) {
    console.error("Failed to load settings:", error);
    return DEFAULT_SETTINGS;
  }
};

export const saveAppSettings = (settings: AppSettings): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch (error) {
    console.error("Failed to save settings:", error);
  }
};
