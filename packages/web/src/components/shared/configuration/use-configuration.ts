import { useState, useMemo } from "react";
import {
  validateComponentConfig,
  getComponentConfigExamples,
} from "./config-validation";
import type { ValidationResult } from "./config-validation";

interface UseConfigurationOptions {
  initialValue?: string;
  componentType?: string;
}

interface UseConfigurationReturn {
  value: string;
  setValue: (value: string) => void;
  parsedValue: unknown;
  validationResult: ValidationResult;
  isValid: boolean;
  examples: Array<{ description: string; value: string }>;
  reset: () => void;
  loadFromObject: (obj: unknown) => void;
}

/**
 * Validates configuration value and returns parsed result
 */
export function validateConfiguration(
  value: string,
  componentType: string,
): { parsedValue: unknown; validationResult: ValidationResult } {
  if (!value.trim()) {
    return {
      parsedValue: undefined,
      validationResult: {
        isValid: true,
        errors: [],
        warnings: [],
      },
    };
  }

  try {
    const parsed = JSON.parse(value);

    const result = componentType
      ? validateComponentConfig(parsed, componentType)
      : { isValid: true, errors: [], warnings: [] };

    return {
      parsedValue: parsed,
      validationResult: result,
    };
  } catch (error) {
    return {
      parsedValue: undefined,
      validationResult: {
        isValid: false,
        errors: [
          error instanceof Error ? error.message : "Invalid JSON format",
        ],
        warnings: [],
      },
    };
  }
}

/**
 * Hook for managing JSON configuration state with validation
 */
export function useConfiguration({
  initialValue = "",
  componentType = "",
}: UseConfigurationOptions = {}): UseConfigurationReturn {
  const [value, setValue] = useState(initialValue);

  const { parsedValue, validationResult } = useMemo(
    () => validateConfiguration(value, componentType),
    [value, componentType],
  );

  const examples = useMemo(() => {
    return componentType ? getComponentConfigExamples(componentType) : [];
  }, [componentType]);

  const reset = () => setValue(initialValue);

  const loadFromObject = (obj: unknown) => {
    try {
      const jsonString = JSON.stringify(obj, null, 2);
      setValue(jsonString);
    } catch (error) {
      console.error("Failed to convert object to JSON:", error);
    }
  };

  return {
    value,
    setValue,
    parsedValue,
    validationResult,
    isValid: validationResult.isValid,
    examples,
    reset,
    loadFromObject,
  };
}
