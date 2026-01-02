const PREFERENCES_KEY = "shelly-scan-preferences";

export interface ScanPreferences {
  scan_mode: "mdns" | "manual";
  manual_mode: "ips" | "range_cidr";
  timeout: number;
  max_workers: number;
  manual_ips: string;
  range_cidr: string;
}

const DEFAULT_PREFERENCES: ScanPreferences = {
  scan_mode: "manual",
  manual_mode: "range_cidr",
  timeout: 3,
  max_workers: 50,
  manual_ips: "",
  range_cidr: "",
};

export function saveScanPreferences(prefs: Partial<ScanPreferences>) {
  try {
    const existing = loadScanPreferences();
    const updated = { ...existing, ...prefs };
    localStorage.setItem(PREFERENCES_KEY, JSON.stringify(updated));
  } catch (error) {
    console.error("Failed to save scan preferences:", error);
  }
}

export function loadScanPreferences(): ScanPreferences {
  try {
    const stored = localStorage.getItem(PREFERENCES_KEY);
    if (!stored) return DEFAULT_PREFERENCES;

    const parsed = JSON.parse(stored);

    return {
      ...DEFAULT_PREFERENCES,
      ...parsed,
      scan_mode: ["mdns", "manual"].includes(parsed.scan_mode)
        ? parsed.scan_mode
        : DEFAULT_PREFERENCES.scan_mode,
      manual_mode: ["ips", "range_cidr"].includes(parsed.manual_mode)
        ? parsed.manual_mode
        : DEFAULT_PREFERENCES.manual_mode,
    };
  } catch (error) {
    console.error("Failed to load scan preferences:", error);
    return DEFAULT_PREFERENCES;
  }
}
