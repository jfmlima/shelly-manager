import { useState, useEffect, useRef } from "react";
import type { BulkProgress, BulkActionType } from "../types";

// Time estimates for different operations (in milliseconds)
const OPERATION_TIME_ESTIMATES: Record<BulkActionType, number> = {
  update: 3000, // 3 seconds per device
  reboot: 3000, // 3 seconds per device
  factory_reset: 3000, // 3 seconds per device
  export_config: 3000, // 3 seconds per device
  apply_config: 3000, // 3 seconds per device
};

const PROGRESS_UPDATE_INTERVAL = 1000; // Update every second

export function useBulkProgress() {
  const [progress, setProgressState] = useState<BulkProgress | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

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

  const calculateEstimatedDuration = (
    operationType: BulkActionType,
    deviceCount: number,
  ): number => {
    const baseTimePerDevice = OPERATION_TIME_ESTIMATES[operationType];
    // Add some overhead for network latency and processing
    const overheadFactor = 1.2;
    return Math.ceil(baseTimePerDevice * deviceCount * overheadFactor);
  };

  const calculateTimeBasedProgress = (
    startTime: number,
    estimatedDuration: number,
    currentTime: number,
  ): number => {
    const elapsed = currentTime - startTime;
    const progressRatio = elapsed / estimatedDuration;

    if (progressRatio < 0.7) {
      return Math.min(70, progressRatio * 100);
    } else {
      const remainingProgress = 30;
      const remainingTimeRatio = (progressRatio - 0.7) / 0.3;
      return 70 + remainingProgress * remainingTimeRatio;
    }
  };

  const startProgressTimer = (
    operationType: BulkActionType,
    deviceCount: number,
  ) => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    const startTime = Date.now();
    const estimatedDuration = calculateEstimatedDuration(
      operationType,
      deviceCount,
    );

    timerRef.current = setInterval(() => {
      const currentTime = Date.now();
      const timeElapsed = currentTime - startTime;

      setProgressState((prevProgress) => {
        if (!prevProgress || !prevProgress.isRunning) {
          return prevProgress;
        }

        const currentProgressPercent = calculateTimeBasedProgress(
          startTime,
          estimatedDuration,
          currentTime,
        );
        const estimatedTimeRemaining = Math.max(
          0,
          estimatedDuration - timeElapsed,
        );

        return {
          ...prevProgress,
          startTime,
          estimatedDurationMs: estimatedDuration,
          currentProgress: Math.min(95, currentProgressPercent), // Cap at 95% until actual completion
          timeElapsedMs: timeElapsed,
          estimatedTimeRemainingMs: estimatedTimeRemaining,
        };
      });
    }, PROGRESS_UPDATE_INTERVAL);
  };

  const stopProgressTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const initializeProgress = (total: number, operationType: BulkActionType) => {
    setProgress({
      total,
      completed: 0,
      failed: 0,
      results: [],
      isRunning: true,
      startTime: Date.now(),
    });
    startProgressTimer(operationType, total);
  };

  const resetProgress = () => {
    stopProgressTimer();
    setProgress(null);
    setShowDetails(false);
  };

  const stopProgress = () => {
    stopProgressTimer();
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
