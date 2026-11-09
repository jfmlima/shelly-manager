import { useMemo, useState } from "react";
import { Save, RotateCcw, Trash2, AlertTriangle, Copy } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { handleApiError } from "@/lib/api";
import {
  useBackup,
  useBackups,
  useBackupsByModel,
  useCreateBackup,
  useDeleteBackup,
  useRestoreBackup,
} from "@/hooks/useBackups";
import { useComponentTypes } from "@/hooks/useComponentTypes";
import { PAGE_SIZE, useRewindEmptyPage } from "@/hooks/useOffsetPagination";
import { OffsetPager } from "@/components/shared/offset-pager";
import type { BackupSummary } from "@/types/api";

interface BackupsSectionProps {
  deviceIp: string;
  deviceMac: string | null;
  deviceName: string | null;
  deviceType: string | null;
  firmwareVersion: string | null;
}

export function BackupsSection({
  deviceIp,
  deviceMac,
  deviceName,
  deviceType,
  firmwareVersion,
}: BackupsSectionProps) {
  const [offset, setOffset] = useState(0);
  const {
    data: backups,
    isLoading,
    isSuccess,
    error,
  } = useBackups(deviceMac, {
    limit: PAGE_SIZE,
    offset,
  });
  const createBackup = useCreateBackup();
  const [restoreTarget, setRestoreTarget] = useState<BackupSummary | null>(
    null,
  );
  const [cloneOpen, setCloneOpen] = useState(false);

  const items = backups?.items ?? [];
  const total = backups?.total ?? 0;

  // A device switch should start from the first page, not inherit the old one.
  const [renderedMac, setRenderedMac] = useState(deviceMac);
  if (renderedMac !== deviceMac) {
    setRenderedMac(deviceMac);
    setOffset(0);
  }

  useRewindEmptyPage(isSuccess, items.length, offset, setOffset);

  const formatDate = (ts: number | null) =>
    ts ? new Date(ts * 1000).toLocaleString() : "-";

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Configuration Backups</CardTitle>
          <CardDescription>
            Snapshot this device's configuration and restore it later.
          </CardDescription>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setCloneOpen(true)}>
            <Copy className="h-4 w-4 mr-2" />
            Restore from another device
          </Button>
          <Button
            onClick={() => createBackup.mutate({ deviceIp, name: undefined })}
            disabled={createBackup.isPending}
          >
            <Save className="h-4 w-4 mr-2" />
            {createBackup.isPending ? "Backing up..." : "Create backup"}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {!deviceMac ? (
          <p className="text-sm text-muted-foreground">
            Device MAC unavailable; backups cannot be listed.
          </p>
        ) : isLoading ? (
          <p className="text-sm text-muted-foreground">Loading backups...</p>
        ) : (
          <>
            {error && (
              <p className="text-sm text-destructive pb-2">
                Failed to load backups: {handleApiError(error)}
              </p>
            )}
            {!error && total === 0 && (
              <p className="text-sm text-muted-foreground">No backups yet.</p>
            )}
            {items.length > 0 && (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Firmware</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {items.map((backup) => (
                      <BackupRow
                        key={backup.id}
                        backup={backup}
                        formatDate={formatDate}
                        onRestore={() => setRestoreTarget(backup)}
                      />
                    ))}
                  </TableBody>
                </Table>
                {total > PAGE_SIZE && (
                  <OffsetPager
                    offset={offset}
                    itemCount={items.length}
                    total={total}
                    onOffsetChange={setOffset}
                  />
                )}
              </>
            )}
          </>
        )}
      </CardContent>

      {restoreTarget && (
        <RestoreDialog
          backup={restoreTarget}
          deviceIp={deviceIp}
          deviceName={deviceName}
          onClose={() => setRestoreTarget(null)}
        />
      )}

      {cloneOpen && (
        <RestoreFromDeviceDialog
          deviceIp={deviceIp}
          deviceMac={deviceMac}
          deviceName={deviceName}
          deviceType={deviceType}
          firmwareVersion={firmwareVersion}
          formatDate={formatDate}
          onClose={() => setCloneOpen(false)}
        />
      )}
    </Card>
  );
}

function BackupRow({
  backup,
  formatDate,
  onRestore,
}: {
  backup: BackupSummary;
  formatDate: (ts: number | null) => string;
  onRestore: () => void;
}) {
  const deleteBackup = useDeleteBackup();
  return (
    <TableRow>
      <TableCell>#{backup.id}</TableCell>
      <TableCell>{formatDate(backup.created_at)}</TableCell>
      <TableCell>{backup.firmware_version ?? "-"}</TableCell>
      <TableCell>{backup.source}</TableCell>
      <TableCell className="text-right space-x-2">
        <Button variant="outline" size="sm" onClick={onRestore}>
          <RotateCcw className="h-4 w-4 mr-1" />
          Restore
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => deleteBackup.mutate(backup.id)}
          disabled={deleteBackup.isPending}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </TableCell>
    </TableRow>
  );
}

function RestoreFromDeviceDialog({
  deviceIp,
  deviceMac,
  deviceName,
  deviceType,
  firmwareVersion,
  formatDate,
  onClose,
}: {
  deviceIp: string;
  deviceMac: string | null;
  deviceName: string | null;
  deviceType: string | null;
  firmwareVersion: string | null;
  formatDate: (ts: number | null) => string;
  onClose: () => void;
}) {
  const [offset, setOffset] = useState(0);
  const { data, isLoading, error } = useBackupsByModel(deviceType, deviceMac, {
    limit: PAGE_SIZE,
    offset,
  });
  const [picked, setPicked] = useState<BackupSummary | null>(null);

  const others = data?.items ?? [];
  const total = data?.total ?? 0;

  if (picked) {
    return (
      <RestoreDialog
        backup={picked}
        deviceIp={deviceIp}
        deviceName={deviceName}
        clone={{ targetFirmware: firmwareVersion }}
        onClose={onClose}
      />
    );
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Restore from another device</DialogTitle>
          <DialogDescription>
            Pick a backup of another device of the same model to apply to{" "}
            {deviceName || deviceIp}.
          </DialogDescription>
        </DialogHeader>

        {!deviceType ? (
          <p className="text-sm text-muted-foreground">
            This device did not report its model, so backups of the same model
            cannot be listed.
          </p>
        ) : isLoading ? (
          <p className="text-sm text-muted-foreground">Loading backups...</p>
        ) : error ? (
          <p className="text-sm text-destructive">
            Failed to load backups: {handleApiError(error)}
          </p>
        ) : others.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No backups from other devices of this model.
          </p>
        ) : (
          <>
            <div className="max-h-96 overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Device</TableHead>
                    <TableHead>MAC</TableHead>
                    <TableHead>Firmware</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {others.map((backup) => (
                    <TableRow key={backup.id}>
                      <TableCell>
                        {backup.device_name || backup.device_ip || "-"}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {backup.device_mac}
                      </TableCell>
                      <TableCell>{backup.firmware_version ?? "-"}</TableCell>
                      <TableCell>{formatDate(backup.created_at)}</TableCell>
                      <TableCell>{backup.source}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setPicked(backup)}
                        >
                          Select
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {total > PAGE_SIZE && (
              <OffsetPager
                offset={offset}
                itemCount={others.length}
                total={total}
                onOffsetChange={setOffset}
              />
            )}
          </>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function RestoreDialog({
  backup,
  deviceIp,
  deviceName,
  clone,
  onClose,
}: {
  backup: BackupSummary;
  deviceIp: string;
  deviceName: string | null;
  clone?: { targetFirmware: string | null };
  onClose: () => void;
}) {
  const restore = useRestoreBackup();
  const { data: detail, isLoading, error } = useBackup(backup.id);
  const {
    componentTypes: vocabulary,
    isLoading: vocabularyLoading,
    usingFallback,
  } = useComponentTypes();

  const networkTypes = useMemo(
    () => new Set(vocabulary.network),
    [vocabulary.network],
  );

  const componentTypes = useMemo(() => {
    const components = detail?.snapshot.components ?? {};
    return Object.entries(components).map(([key, value]) => ({
      key,
      network: isNetworkComponent(key, value.type, networkTypes),
    }));
  }, [detail, networkTypes]);

  const [selected, setSelected] = useState<Set<string> | null>(null);
  const [reboot, setReboot] = useState(false);
  const [keepIdentity, setKeepIdentity] = useState(true);

  const firmwareDiffers =
    !!clone &&
    !!backup.firmware_version &&
    !!clone.targetFirmware &&
    backup.firmware_version !== clone.targetFirmware;

  // Default selection: everything except network components.
  const effectiveSelected = useMemo(() => {
    if (selected) return selected;
    return new Set(componentTypes.filter((c) => !c.network).map((c) => c.key));
  }, [selected, componentTypes]);

  const toggle = (key: string) => {
    const next = new Set(effectiveSelected);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    setSelected(next);
  };

  const handleRestore = () => {
    restore.mutate(
      {
        backupId: backup.id,
        data: {
          device_ip: deviceIp,
          component_keys: Array.from(effectiveSelected),
          reboot,
          ...(clone
            ? { allow_mac_mismatch: true, keep_target_identity: keepIdentity }
            : {}),
        },
      },
      { onSuccess: onClose },
    );
  };

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Restore backup #{backup.id}</DialogTitle>
          <DialogDescription>
            {clone && (
              <>
                This backup comes from another device,{" "}
                {backup.device_name || backup.device_mac}.{" "}
              </>
            )}
            Select which components to restore onto {deviceName || deviceIp}.
            Network components are unchecked by default to avoid losing
            connectivity.
          </DialogDescription>
        </DialogHeader>

        {firmwareDiffers && (
          <p className="text-sm text-amber-600">
            The backup was taken on firmware {backup.firmware_version} and this
            device runs {clone?.targetFirmware}. Either firmware may reject
            settings the other does not know; the result shows this per
            component.
          </p>
        )}

        {isLoading || vocabularyLoading ? (
          <p className="text-sm text-muted-foreground">Loading components...</p>
        ) : (
          <>
            {error && (
              <p className="text-sm text-destructive">
                Failed to load this backup: {handleApiError(error)}
                {detail ? " Showing the components last loaded." : ""}
              </p>
            )}
            {usingFallback && (
              <p className="text-sm text-amber-600">
                Could not load the network component list from the server, so
                the defaults below come from a built-in list. Check the network
                marks before restoring.
              </p>
            )}
            <div className="max-h-72 overflow-y-auto space-y-2">
              {componentTypes.map((c) => (
                <div key={c.key} className="flex items-center gap-2">
                  <Checkbox
                    id={`restore-${c.key}`}
                    checked={effectiveSelected.has(c.key)}
                    onCheckedChange={() => toggle(c.key)}
                  />
                  <Label
                    htmlFor={`restore-${c.key}`}
                    className="flex items-center gap-2 font-normal"
                  >
                    {c.key}
                    {c.network && (
                      <span className="inline-flex items-center gap-1 text-xs text-amber-600">
                        <AlertTriangle className="h-3 w-3" />
                        network (may disconnect)
                      </span>
                    )}
                  </Label>
                </div>
              ))}
            </div>
          </>
        )}

        {clone && (
          <div className="flex items-center gap-2 pt-2">
            <Checkbox
              id="restore-keep-identity"
              checked={keepIdentity}
              onCheckedChange={(v) => setKeepIdentity(v === true)}
            />
            <Label htmlFor="restore-keep-identity" className="font-normal">
              Keep this device's name and MQTT ids
            </Label>
          </div>
        )}

        <div className="flex items-center gap-2 pt-2">
          <Checkbox
            id="restore-reboot"
            checked={reboot}
            onCheckedChange={(v) => setReboot(v === true)}
          />
          <Label htmlFor="restore-reboot" className="font-normal">
            Reboot device after restore
          </Label>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleRestore}
            disabled={restore.isPending || effectiveSelected.size === 0}
          >
            {restore.isPending ? "Restoring..." : "Restore selected"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Either signal is enough to treat a component as network: an entry can reach
// the store untyped, and a type the device spells differently would otherwise
// win over the key and leave wifi selected for restore.
function isNetworkComponent(
  key: string,
  type: string | null | undefined,
  networkTypes: Set<string>,
) {
  const keyType = key.split(":")[0].toLowerCase();
  return (
    networkTypes.has((type ?? "").toLowerCase()) || networkTypes.has(keyType)
  );
}
