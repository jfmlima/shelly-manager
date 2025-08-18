import { Link, useLocation } from "react-router-dom";
import { Settings, Home } from "lucide-react";
import { useTranslation } from "react-i18next";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function Navbar() {
  const { t } = useTranslation();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Brand */}
          <div className="flex items-center space-x-4">
            <Link to="/" className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">
                  SM
                </span>
              </div>
              <span className="font-semibold text-lg">Shelly Manager</span>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            <Button
              variant={isActive("/") ? "default" : "ghost"}
              size="sm"
              asChild
              className={cn(
                "flex items-center space-x-2",
                isActive("/") && "bg-primary text-primary-foreground",
              )}
            >
              <Link to="/">
                <Home className="h-4 w-4" />
                <span>{t("navigation.dashboard")}</span>
              </Link>
            </Button>

            <Button
              variant={isActive("/settings") ? "default" : "ghost"}
              size="sm"
              asChild
              className={cn(
                "flex items-center space-x-2",
                isActive("/settings") && "bg-primary text-primary-foreground",
              )}
            >
              <Link to="/settings">
                <Settings className="h-4 w-4" />
                <span>{t("navigation.settings")}</span>
              </Link>
            </Button>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-2">
            <ThemeToggle />
          </div>
        </div>
      </div>
    </nav>
  );
}
