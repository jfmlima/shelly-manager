// The scope is spelled out because key hashing drops undefined values, so a
// device list still waiting for its MAC would otherwise share a cache entry
// with the list of every device's backups.
export type BackupListFilters = { limit: number; offset: number } & (
  | { scope: "all" }
  | { scope: "device"; deviceMac: string | null }
);

export const queryKeys = {
  devices: {
    scan: () => ["devices", "scan"] as const,
    status: (ip: string | undefined) => ["devices", "status", ip] as const,
  },
  backups: {
    all: () => ["backups"] as const,
    lists: () => [...queryKeys.backups.all(), "list"] as const,
    list: (filters: BackupListFilters) =>
      [...queryKeys.backups.lists(), filters] as const,
    details: () => [...queryKeys.backups.all(), "detail"] as const,
    detail: (backupId: number) =>
      [...queryKeys.backups.details(), backupId] as const,
  },
  backupSchedules: {
    all: () => ["backup-schedules"] as const,
  },
  credentials: {
    all: () => ["credentials"] as const,
  },
  provisioning: {
    profiles: () => ["provisioning", "profiles"] as const,
  },
  metadata: {
    componentTypes: () => ["metadata", "component-types"] as const,
  },
};
