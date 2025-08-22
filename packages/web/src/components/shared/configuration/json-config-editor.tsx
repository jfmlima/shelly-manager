import { useState, useEffect } from "react";
import { AlertTriangle, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface JsonConfigEditorProps {
  value: string;
  onChange: (value: string) => void;
  onValidChange?: (isValid: boolean, parsedValue?: unknown) => void;
  placeholder?: string;
  label?: string;
  description?: string;
  examples?: Array<{ description: string; value: string }>;
  className?: string;
  disabled?: boolean;
}

export function JsonConfigEditor({
  value,
  onChange,
  onValidChange,
  placeholder = `{
  "enable": true,
  "name": "Component Name"
}`,
  label = "Configuration (JSON)",
  description = "Enter the component configuration as JSON. Only changed fields need to be included.",
  examples = [
    { description: "Enable component", value: '{"enable": true}' },
    {
      description: "Set display name",
      value: '{"name": "Living Room Switch"}',
    },
    { description: "Set initial state", value: '{"initial_state": "on"}' },
  ],
  className = "",
  disabled = false,
}: JsonConfigEditorProps) {
  const [validationError, setValidationError] = useState<string>("");
  const [isValid, setIsValid] = useState(true);

  useEffect(() => {
    if (!value.trim()) {
      setValidationError("");
      setIsValid(true);
      onValidChange?.(true, undefined);
      return;
    }

    try {
      const parsed = JSON.parse(value);
      setValidationError("");
      setIsValid(true);
      onValidChange?.(true, parsed);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Invalid JSON format";
      setValidationError(errorMessage);
      setIsValid(false);
      onValidChange?.(false, undefined);
    }
  }, [value, onValidChange]);

  const handleExampleClick = (exampleValue: string) => {
    if (isValid && value.trim()) {
      try {
        const existing = JSON.parse(value);
        const example = JSON.parse(exampleValue);
        const merged = { ...existing, ...example };
        onChange(JSON.stringify(merged, null, 2));
      } catch {
        onChange(exampleValue);
      }
    } else {
      onChange(exampleValue);
    }
  };

  const formatJson = () => {
    if (isValid && value.trim()) {
      const parsed = JSON.parse(value);
      onChange(JSON.stringify(parsed, null, 2));
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div>
        <div className="flex items-center justify-between mb-2">
          <Label htmlFor="json-config">{label}</Label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={formatJson}
            disabled={!isValid || !value.trim() || disabled}
            className="text-xs"
          >
            Format JSON
          </Button>
        </div>

        {description && (
          <p className="text-sm text-muted-foreground mb-2">{description}</p>
        )}

        <textarea
          id="json-config"
          className={`w-full h-32 p-3 border rounded-lg font-mono text-sm ${
            !isValid ? "border-red-500" : ""
          }`}
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
        />
      </div>

      {/* Validation Error */}
      {validationError && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <strong>JSON Error:</strong> {validationError}
          </AlertDescription>
        </Alert>
      )}

      {/* Examples */}
      {examples.length > 0 && (
        <div className="p-3 bg-muted rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <Info className="h-4 w-4 text-muted-foreground" />
            <p className="text-sm font-medium">Quick Examples:</p>
          </div>
          <div className="space-y-2">
            {examples.map((example, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  {example.description}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => handleExampleClick(example.value)}
                  disabled={disabled}
                  className="text-xs h-6 px-2"
                >
                  Apply
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
