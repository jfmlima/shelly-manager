import { useTranslation } from "react-i18next";
import { formatDistanceToNow } from "date-fns";
import { Clock, AlertTriangle } from "lucide-react";
import { getLastScanTimestamp, isDataStale } from "@/lib/storage";

interface ScanTimestampProps {
  className?: string;
}

export function ScanTimestamp({ className }: ScanTimestampProps) {
  const { t } = useTranslation();

  const lastScanTime = getLastScanTimestamp();
  const isStale = isDataStale();

  if (!lastScanTime) {
    return null;
  }

  const timeAgo = formatDistanceToNow(lastScanTime, { addSuffix: true });

  return (
    <div
      className={`flex items-center space-x-2 text-sm text-muted-foreground ${className || ""}`}
    >
      <div className="flex items-center space-x-1">
        <Clock className="h-4 w-4" />
        <span>
          {t("dashboard.lastScanned", "Last scanned")}: {timeAgo}
        </span>
      </div>

      {isStale && (
        <div className="relative group">
          <AlertTriangle className="h-4 w-4 text-amber-600 cursor-help" />
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
            {t(
              "dashboard.staleData",
              "Data older than 2 days, consider re-scanning.",
            )}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      )}
    </div>
  );
}
