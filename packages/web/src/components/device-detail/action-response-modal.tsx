import { useState, type JSX } from "react";
import {
  Copy,
  Download,
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  Info,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ComponentActionResult } from "@/types/api";

interface ActionResponseModalProps {
  isOpen: boolean;
  onClose: () => void;
  response: ComponentActionResult | null;
  componentType?: string;
}

export function ActionResponseModal({
  isOpen,
  onClose,
  response,
  componentType,
}: ActionResponseModalProps) {
  const [showRawData, setShowRawData] = useState(false);

  if (!response) return null;

  const handleCopyToClipboard = async () => {
    try {
      const dataToString = response.data
        ? JSON.stringify(response.data, null, 2)
        : response.message || "No data";

      await navigator.clipboard.writeText(dataToString);
      toast.success("Response data copied to clipboard");
    } catch {
      toast.error("Failed to copy to clipboard");
    }
  };

  const handleDownloadAsJson = () => {
    try {
      const dataToExport = {
        action: response.action,
        component: response.component_key,
        device: response.ip,
        timestamp: new Date().toISOString(),
        success: response.success,
        message: response.message,
        data: response.data,
        error: response.error,
      };

      const blob = new Blob([JSON.stringify(dataToExport, null, 2)], {
        type: "application/json",
      });

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${response.component_key}-${response.action}-response.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success("Response data downloaded");
    } catch {
      toast.error("Failed to download response data");
    }
  };

  const formatActionName = (action: string) => {
    return action.replace(/([A-Z])/g, " $1").trim();
  };

  const renderFormattedData = (data: unknown) => {
    if (!data || typeof data !== "object") {
      return (
        <div className="text-sm text-muted-foreground">No data available</div>
      );
    }

    const entries = Object.entries(data);

    return (
      <ScrollArea className="w-full rounded-md border h-120">
        <div className="p-4 space-y-3">
          {entries.map(([key, value]) => (
            <div
              key={key}
              className="grid grid-cols-1 md:grid-cols-3 gap-2 py-2 border-b border-border/50 last:border-0"
            >
              <div className="text-sm font-medium text-foreground">
                {key
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (l) => l.toUpperCase())}
              </div>
              <div className="md:col-span-2 text-sm text-muted-foreground font-mono break-all">
                {typeof value === "object" && value !== null ? (
                  <details className="group">
                    <summary className="cursor-pointer hover:text-foreground transition-colors">
                      <span className="text-xs text-muted-foreground/70">
                        [Object] Click to expand
                      </span>
                    </summary>
                    <pre className="mt-2 text-xs bg-muted p-2 rounded whitespace-pre-wrap">
                      {JSON.stringify(value, null, 2)}
                    </pre>
                  </details>
                ) : (
                  <span className="break-words">{String(value)}</span>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="absolute top-2 right-2 text-xs text-muted-foreground bg-background/80 px-2 py-1 rounded">
          {entries.length} {entries.length === 1 ? "field" : "fields"}
        </div>
      </ScrollArea>
    );
  };

  const renderRawData = (data: unknown) => {
    if (!data) {
      return (
        <div className="text-sm text-muted-foreground">No data available</div>
      );
    }

    const formattedJson = JSON.stringify(data, null, 2);

    return (
      <div className="relative">
        <ScrollArea className="w-full rounded-md border h-96">
          <pre className="text-xs font-mono p-4 whitespace-pre-wrap break-words leading-relaxed">
            {formattedJson}
          </pre>
        </ScrollArea>
        <div className="absolute top-2 right-2 text-xs text-muted-foreground bg-background/80 px-2 py-1 rounded">
          {formattedJson.split("\n").length} lines
        </div>
      </div>
    );
  };

  const renderMessage = (): JSX.Element | null => {
    if (!response?.message) return null;

    return (
      <div className="flex items-start space-x-2 p-3 bg-blue-50 dark:bg-blue-950/50 rounded-lg">
        <Info className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-blue-700 dark:text-blue-300">
          {String(response.message)}
        </div>
      </div>
    );
  };

  const renderError = (): JSX.Element | null => {
    if (!response?.error) return null;

    return (
      <div className="flex items-start space-x-2 p-3 bg-red-50 dark:bg-red-950/50 rounded-lg">
        <XCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-red-700 dark:text-red-300">
          {String(response.error)}
        </div>
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl min-w-1/2 max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            {response.success ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <XCircle className="h-5 w-5 text-red-500" />
            )}
            <span>Action Response: {formatActionName(response.action)}</span>
          </DialogTitle>
          <DialogDescription>
            Response from {response.component_key} on device {response.ip}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 pr-4 h-120 w-full">
          <div className="space-y-4">
            {/* Status and Actions */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Badge variant={response.success ? "default" : "destructive"}>
                  {response.success ? "Success" : "Failed"}
                </Badge>
                {componentType && (
                  <Badge variant="outline">{componentType}</Badge>
                )}
              </div>

              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowRawData(!showRawData)}
                >
                  {showRawData ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                  {showRawData ? "Formatted" : "Raw"}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyToClipboard}
                >
                  <Copy className="h-4 w-4" />
                  Copy
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownloadAsJson}
                >
                  <Download className="h-4 w-4" />
                  Export
                </Button>
              </div>
            </div>

            {renderMessage()}
            {renderError()}

            {response.data && (
              <>
                <Separator />
                <div>
                  <h4 className="text-sm font-medium mb-3">Response Data</h4>
                  {showRawData
                    ? renderRawData(response.data)
                    : renderFormattedData(response.data)}
                </div>
              </>
            )}

            {/* No Data Message */}
            {!response.data && response.success && (
              <div className="text-center py-8 text-muted-foreground">
                <Info className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  Action completed successfully with no data returned
                </p>
              </div>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
