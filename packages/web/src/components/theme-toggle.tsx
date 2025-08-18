import { Moon, Sun } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/theme-provider";

export function ThemeToggle() {
  const { t } = useTranslation();
  const { theme, setTheme } = useTheme();

  const toggleTheme = () => {
    if (theme === "light") {
      setTheme("dark");
    } else if (theme === "dark") {
      setTheme("system");
    } else {
      setTheme("light");
    }
  };

  const getIcon = () => {
    if (theme === "light") return <Sun className="h-[1.2rem] w-[1.2rem]" />;
    if (theme === "dark") return <Moon className="h-[1.2rem] w-[1.2rem]" />;
    return <Sun className="h-[1.2rem] w-[1.2rem]" />; // System default to sun
  };

  const getTitle = () => {
    if (theme === "light") return t("ui.switchToDarkMode");
    if (theme === "dark") return t("ui.switchToSystemMode");
    return t("ui.switchToLightMode");
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleTheme}
      title={getTitle()}
      className="h-8 w-8 px-0"
    >
      {getIcon()}
      <span className="sr-only">{t("ui.toggleTheme")}</span>
    </Button>
  );
}
