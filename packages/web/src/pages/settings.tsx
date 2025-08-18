import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Settings as SettingsIcon, Palette, Server, Table } from "lucide-react";

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
import { useTheme } from "@/components/theme-provider";
import { toast } from "sonner";

interface SettingsData {
  tablePageSize: number;
  tableDensity: "compact" | "normal" | "comfortable";
}

export function Settings() {
  const { t } = useTranslation();
  const { theme, setTheme } = useTheme();
  const [settings, setSettings] = useState<SettingsData>({
    tablePageSize: 10,
    tableDensity: "normal",
  });

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

  const baseApiUrl =
    import.meta.env.VITE_BASE_API_URL || "http://localhost:8000";

  return (
    <div className="space-y-6">
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
              <span>{t("settings.api.title")}</span>
            </CardTitle>
            <CardDescription>{t("settings.api.description")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>{t("settings.api.baseUrl")}</Label>
              <Input
                value={baseApiUrl}
                disabled
                className="font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground">
                {t("settings.api.urlDescription")}
              </p>
            </div>

            <div className="p-3 bg-muted rounded-lg">
              <div className="text-sm font-medium mb-1">
                {t("settings.api.connectionStatus")}
              </div>
              <div className="text-xs text-muted-foreground">
                {t("settings.api.apiEndpoint")}: {baseApiUrl}/api
              </div>
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
            <CardDescription>{t("settings.table.description")}</CardDescription>
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
                onValueChange={(value: "compact" | "normal" | "comfortable") =>
                  updateSetting("tableDensity", value)
                }
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

        {/* Network Presets - Placeholder */}
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

      {/* Footer info */}
      <Card>
        <CardContent className="pt-6">
          <div className="text-center space-y-2">
            <h3 className="font-semibold">{t("settings.footer.title")}</h3>
            <p className="text-sm text-muted-foreground">
              {t("settings.footer.description")}
            </p>
            <div className="text-xs text-muted-foreground space-x-4">
              <span>{t("settings.footer.builtWith")}</span>
              <span>•</span>
              <span>{t("settings.footer.poweredBy")}</span>
              <span>•</span>
              <span>{t("settings.footer.uiBy")}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
