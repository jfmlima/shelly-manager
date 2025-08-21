import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  Settings as SettingsIcon,
  Palette,
  Server,
  Table,
  Check,
  X,
  Loader2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Footer } from "@/components/ui/footer";
import { useTheme } from "@/components/theme-provider";
import { toast } from "sonner";
import { validateApiUrl } from "@/lib/api";

interface SettingsData {
  tablePageSize: number;
  tableDensity: "compact" | "normal" | "comfortable";
}

interface ApiConnectionStatus {
  status: "checking" | "connected" | "error" | "unknown";
  message?: string;
}

export function Settings() {
  const { t } = useTranslation();
  const { theme, setTheme } = useTheme();
  const [settings, setSettings] = useState<SettingsData>({
    tablePageSize: 10,
    tableDensity: "normal",
  });

  const [apiUrl, setApiUrl] = useState("");
  const [tempApiUrl, setTempApiUrl] = useState("");
  const [connectionStatus, setConnectionStatus] = useState<ApiConnectionStatus>(
    {
      status: "unknown",
    },
  );

  useEffect(() => {
    const savedSettings = localStorage.getItem("shelly-manager-settings");
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(parsed);
      } catch (error) {
        console.error(t("settings.messages.failedToParse"), error);
      }
    }

    const savedApiUrl = localStorage.getItem("shelly-manager-api-url");
    const defaultApiUrl =
      import.meta.env.VITE_BASE_API_URL || "http://localhost:8000";
    const currentApiUrl = savedApiUrl || defaultApiUrl;

    setApiUrl(currentApiUrl);
    setTempApiUrl(currentApiUrl);
  }, [t]);

  const saveSettings = () => {
    localStorage.setItem("shelly-manager-settings", JSON.stringify(settings));
    toast.success(t("settings.messages.settingsSaved"));
  };

  const updateSetting = <K extends keyof SettingsData>(
    key: K,
    value: SettingsData[K],
  ) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const testApiConnection = async (url: string) => {
    setConnectionStatus({ status: "checking" });

    try {
      const sanitizedUrl = url.replace(/\/+$/, ""); // Remove trailing slashes
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(`${sanitizedUrl}/api/health`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        setConnectionStatus({
          status: "connected",
          message: `Connected successfully (${data.status || "OK"})`,
        });
        return true;
      } else {
        setConnectionStatus({
          status: "error",
          message: `HTTP ${response.status}: ${response.statusText}`,
        });
        return false;
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      setConnectionStatus({
        status: "error",
        message: `Connection failed: ${errorMessage}`,
      });
      return false;
    }
  };

  const saveApiUrl = async () => {
    if (!validateCurrentUrl()) {
      return;
    }

    const isValid = await testApiConnection(tempApiUrl);
    if (isValid) {
      localStorage.setItem("shelly-manager-api-url", tempApiUrl);
      setApiUrl(tempApiUrl);
      toast.success("API URL saved successfully");
      setTimeout(() => window.location.reload(), 1000);
    } else {
      toast.error("Cannot save API URL - connection test failed");
    }
  };

  const resetApiUrl = () => {
    const defaultApiUrl =
      import.meta.env.VITE_BASE_API_URL || "http://localhost:8000";
    setTempApiUrl(defaultApiUrl);
    localStorage.removeItem("shelly-manager-api-url");
    setApiUrl(defaultApiUrl);
    setConnectionStatus({ status: "unknown" });
    toast.success("API URL reset to default");
    setTimeout(() => window.location.reload(), 1000);
  };

  const validateCurrentUrl = () => {
    const validation = validateApiUrl(tempApiUrl);
    if (!validation.valid) {
      toast.error(validation.error || "Invalid URL");
      return false;
    }
    return true;
  };

  const getPresetUrls = () => {
    const currentHost = window.location.hostname;
    return [
      `http://${currentHost}:8000`,
      "http://localhost:8000",
      "http://192.168.1.100:8000",
      "http://192.168.0.100:8000",
    ].filter((url, index, self) => self.indexOf(url) === index);
  };

  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col">
      {/* Main Content */}
      <div className="flex-1 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {t("settings.title")}
          </h1>
          <p className="text-muted-foreground">{t("settings.subtitle")}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Appearance Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Palette className="h-5 w-5" />
                <span>{t("settings.appearance.title")}</span>
              </CardTitle>
              <CardDescription>
                {t("settings.appearance.description")}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>{t("settings.appearance.theme")}</Label>
                <Select value={theme} onValueChange={setTheme}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 rounded-full bg-white border-2 border-gray-200"></div>
                        <span>{t("settings.appearance.light")}</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="dark">
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 rounded-full bg-gray-900 border-2 border-gray-700"></div>
                        <span>{t("settings.appearance.dark")}</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="system">
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 rounded-full bg-gradient-to-r from-white to-gray-900 border-2 border-gray-400"></div>
                        <span>{t("settings.appearance.system")}</span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {t("settings.appearance.themeDescription")}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* API Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Server className="h-5 w-5" />
                <span>API Configuration</span>
              </CardTitle>
              <CardDescription>
                Configure API server connection for mobile and remote access
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>API Server URL</Label>
                <div className="flex space-x-2">
                  <Input
                    value={tempApiUrl}
                    onChange={(e) => setTempApiUrl(e.target.value)}
                    placeholder="http://192.168.1.100:8000"
                    className="font-mono text-sm"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => testApiConnection(tempApiUrl)}
                    disabled={connectionStatus.status === "checking"}
                  >
                    {connectionStatus.status === "checking" ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      "Test"
                    )}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Enter the IP address or hostname where your API server is
                  running
                </p>
              </div>

              {/* Connection Status */}
              <div
                className={`p-3 rounded-lg border ${
                  connectionStatus.status === "connected"
                    ? "bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800"
                    : connectionStatus.status === "error"
                      ? "bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800"
                      : "bg-muted"
                }`}
              >
                <div className="flex items-center space-x-2">
                  {connectionStatus.status === "checking" && (
                    <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                  )}
                  {connectionStatus.status === "connected" && (
                    <Check className="h-4 w-4 text-green-600" />
                  )}
                  {connectionStatus.status === "error" && (
                    <X className="h-4 w-4 text-red-600" />
                  )}
                  <div className="text-sm font-medium">
                    {connectionStatus.status === "checking" &&
                      "Testing connection..."}
                    {connectionStatus.status === "connected" && "Connected"}
                    {connectionStatus.status === "error" && "Connection failed"}
                    {connectionStatus.status === "unknown" &&
                      "Connection status unknown"}
                  </div>
                </div>
                {connectionStatus.message && (
                  <div className="text-xs text-muted-foreground mt-1">
                    {connectionStatus.message}
                  </div>
                )}
              </div>

              {/* Quick Presets */}
              <div className="space-y-2">
                <Label className="text-xs">Quick presets:</Label>
                <div className="flex flex-wrap gap-1">
                  {getPresetUrls().map((url) => (
                    <Button
                      key={url}
                      variant="outline"
                      size="sm"
                      className="h-7 px-2 text-xs font-mono"
                      onClick={() => setTempApiUrl(url)}
                    >
                      {url.replace(/^https?:\/\//, "")}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-2">
                <Button
                  onClick={saveApiUrl}
                  className="flex-1"
                  disabled={!tempApiUrl || tempApiUrl === apiUrl}
                >
                  Save & Apply
                </Button>
                <Button
                  variant="outline"
                  onClick={resetApiUrl}
                  disabled={!localStorage.getItem("shelly-manager-api-url")}
                >
                  Reset
                </Button>
              </div>

              <div className="text-xs text-muted-foreground">
                Current: {apiUrl}/api
              </div>
            </CardContent>
          </Card>

          {/* Table Preferences */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Table className="h-5 w-5" />
                <span>{t("settings.table.title")}</span>
              </CardTitle>
              <CardDescription>
                {t("settings.table.description")}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>{t("settings.table.pageSize")}</Label>
                <Select
                  value={settings.tablePageSize.toString()}
                  onValueChange={(value) =>
                    updateSetting("tablePageSize", parseInt(value))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="5">5 rows</SelectItem>
                    <SelectItem value="10">10 rows</SelectItem>
                    <SelectItem value="20">20 rows</SelectItem>
                    <SelectItem value="50">50 rows</SelectItem>
                    <SelectItem value="100">100 rows</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>{t("settings.table.density")}</Label>
                <Select
                  value={settings.tableDensity}
                  onValueChange={(
                    value: "compact" | "normal" | "comfortable",
                  ) => updateSetting("tableDensity", value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="compact">
                      {t("settings.table.compact")}
                    </SelectItem>
                    <SelectItem value="normal">
                      {t("settings.table.normal")}
                    </SelectItem>
                    <SelectItem value="comfortable">
                      {t("settings.table.comfortable")}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button onClick={saveSettings} className="w-full">
                {t("settings.table.savePreferences")}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <SettingsIcon className="h-5 w-5" />
                <span>{t("settings.networkPresets.title")}</span>
              </CardTitle>
              <CardDescription>
                {t("settings.networkPresets.description")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <SettingsIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  {t("settings.networkPresets.configuration")}
                </p>
                <p className="text-xs">
                  {t("settings.networkPresets.comingSoon")}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Sticky Footer */}
      <Footer className="mt-6" />
    </div>
  );
}
