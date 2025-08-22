import { useState } from "react";
import type { BulkProgress } from "../types";

export function useBulkProgress() {
  const [progress, setProgressState] = useState<BulkProgress | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const setProgress = (
    value:
      | BulkProgress
      | null
      | ((prev: BulkProgress | null) => BulkProgress | null),
  ) => {
    if (typeof value === "function") {
      setProgressState(value);
    } else {
      setProgressState(value);
    }
  };

  const initializeProgress = (total: number) => {
    setProgress({
      total,
      completed: 0,
      failed: 0,
      results: [],
      isRunning: true,
    });
  };

  const resetProgress = () => {
    setProgress(null);
    setShowDetails(false);
  };

  const stopProgress = () => {
    setProgress((prev) => (prev ? { ...prev, isRunning: false } : null));
  };

  return {
    progress,
    setProgress,
    showDetails,
    setShowDetails,
    initializeProgress,
    resetProgress,
    stopProgress,
  };
}
