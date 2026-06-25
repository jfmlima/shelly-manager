import type { CreateBackupScheduleRequest, BackupSchedule } from "@/types/api";

export type Cadence = "hourly" | "daily" | "weekly" | "custom";

export interface ScheduleFormState {
  name: string;
  cadence: Cadence;
  intervalSeconds: string;
  targetIps: string;
  targetMacs: string;
  allCredentialed: boolean;
  enabled: boolean;
  keepLast: string;
  maxAgeDays: string;
}

export const EMPTY_FORM: ScheduleFormState = {
  name: "",
  cadence: "daily",
  intervalSeconds: "3600",
  targetIps: "",
  targetMacs: "",
  allCredentialed: false,
  enabled: true,
  keepLast: "",
  maxAgeDays: "",
};

const CADENCE_SECONDS: Record<Exclude<Cadence, "custom">, number> = {
  hourly: 3600,
  daily: 86400,
  weekly: 604800,
};

export function scheduleToForm(schedule: BackupSchedule): ScheduleFormState {
  const preset = (Object.entries(CADENCE_SECONDS).find(
    ([, seconds]) => seconds === schedule.interval_seconds,
  )?.[0] ?? "custom") as Cadence;
  return {
    name: schedule.name,
    cadence: preset,
    intervalSeconds: String(schedule.interval_seconds),
    targetIps: schedule.target_ips.join(", "),
    targetMacs: schedule.target_macs.join(", "),
    allCredentialed: schedule.all_credentialed,
    enabled: schedule.enabled,
    keepLast:
      schedule.retention_keep_last != null
        ? String(schedule.retention_keep_last)
        : "",
    maxAgeDays:
      schedule.retention_max_age_days != null
        ? String(schedule.retention_max_age_days)
        : "",
  };
}

function splitList(raw: string): string[] {
  return raw
    .split(/[\s,]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

/** Build a request payload, or return an error string if the form is invalid. */
export function formToRequest(
  form: ScheduleFormState,
): { request: CreateBackupScheduleRequest } | { error: string } {
  const name = form.name.trim();
  if (!name) {
    return { error: "Name is required" };
  }

  const targetIps = splitList(form.targetIps);
  const targetMacs = splitList(form.targetMacs);
  if (!targetIps.length && !targetMacs.length && !form.allCredentialed) {
    return {
      error: "Add at least one target IP, MAC, or enable all-credentialed",
    };
  }

  const request: CreateBackupScheduleRequest = {
    name,
    target_ips: targetIps,
    target_macs: targetMacs,
    all_credentialed: form.allCredentialed,
    enabled: form.enabled,
    retention_keep_last: form.keepLast ? Number(form.keepLast) : null,
    retention_max_age_days: form.maxAgeDays ? Number(form.maxAgeDays) : null,
  };

  if (form.cadence === "custom") {
    const interval = Number(form.intervalSeconds);
    if (!Number.isFinite(interval) || interval < 60) {
      return { error: "Custom interval must be at least 60 seconds" };
    }
    request.interval_seconds = interval;
  } else {
    request.every = form.cadence;
  }

  return { request };
}
