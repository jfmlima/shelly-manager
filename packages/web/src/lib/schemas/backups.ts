import { z } from "zod";

const configBlobSchema = z.record(z.string(), z.unknown());

// Each field degrades on its own so that a component whose payload cannot be
// read keeps its type: the restore dialog leaves network components unchecked
// by type, and a lost type would silently offer to overwrite wifi or cloud.
export const componentSnapshotSchema = z
  .object({
    type: z.string().nullish().catch(null),
    success: z.boolean().optional().catch(undefined),
    config: configBlobSchema.nullish().catch(null),
    error: z.string().nullish().catch(null),
    code: configBlobSchema.nullish().catch(null),
  })
  .catch({});

export const snapshotDeviceInfoSchema = z
  .object({
    device_name: z.string().nullish(),
    device_type: z.string().nullish(),
    firmware_version: z.string().nullish(),
    mac_address: z.string().nullish(),
    app_name: z.string().nullish(),
  })
  .catch({});

export const deviceSnapshotSchema = z
  .object({
    device_info: snapshotDeviceInfoSchema.default({}),
    components: z.record(z.string(), componentSnapshotSchema).default({}),
  })
  .catch({ device_info: {}, components: {} });

export const backupSummarySchema = z.object({
  id: z.number(),
  device_mac: z.string(),
  device_ip: z.string().nullable().default(null),
  device_name: z.string().nullable().default(null),
  device_type: z.string().nullable().default(null),
  firmware_version: z.string().nullable().default(null),
  generation: z.string().default("gen2"),
  name: z.string().nullable().default(null),
  source: z.string().default("manual"),
  sha256: z.string().nullable().default(null),
  size_bytes: z.number().default(0),
  created_at: z.number().nullable().default(null),
});

export const backupDetailSchema = backupSummarySchema.extend({
  snapshot: deviceSnapshotSchema.default({ device_info: {}, components: {} }),
});

// items and total are required: the API always sends them, and defaulting
// them would turn any unrelated JSON body into a convincing empty page.
export const paginatedBackupsSchema = z.object({
  items: z.array(backupSummarySchema),
  total: z.number(),
  limit: z.number().default(50),
  offset: z.number().default(0),
});

export const componentRestoreResultSchema = z.object({
  key: z.string(),
  action: z.string(),
  success: z.boolean(),
  skipped: z.boolean().default(false),
  skipped_reason: z.string().nullable().default(null),
  error: z.string().nullable().default(null),
});

export const restoreResultSchema = z.object({
  success: z.boolean(),
  device_ip: z.string(),
  backup_id: z.number(),
  total: z.number(),
  succeeded: z.number().default(0),
  failed: z.number().default(0),
  skipped: z.number().default(0),
  message: z.string().nullable().default(null),
  components: z.array(componentRestoreResultSchema).default([]),
});

export type ComponentSnapshot = z.infer<typeof componentSnapshotSchema>;
export type DeviceSnapshot = z.infer<typeof deviceSnapshotSchema>;
export type BackupSummary = z.infer<typeof backupSummarySchema>;
export type BackupDetail = z.infer<typeof backupDetailSchema>;
export type PaginatedBackups = z.infer<typeof paginatedBackupsSchema>;
export type ComponentRestoreResult = z.infer<
  typeof componentRestoreResultSchema
>;
export type RestoreResult = z.infer<typeof restoreResultSchema>;
