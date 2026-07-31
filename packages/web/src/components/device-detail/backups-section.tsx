import { useEffect, useMemo, useState } from "react";
import { Save, RotateCcw, Trash2, AlertTriangle } from "lucide-react";

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
}

export function BackupsSection({
  deviceIp,
  deviceMac,
  deviceName,
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

  const items = backups?.items ?? [];
  const total = backups?.total ?? 0;

  // A device switch should start from the first page, not inherit the old one.
  useEffect(() => {
    setOffset(0);
  }, [deviceMac]);

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
        <Button
          onClick={() => createBackup.mutate({ deviceIp, name: undefined })}
          disabled={createBackup.isPending}
        >
          <Save className="h-4 w-4 mr-2" />
          {createBackup.isPending ? "Backing up..." : "Create backup"}
        </Button>
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

function RestoreDialog({
  backup,
  deviceIp,
  deviceName,
  onClose,
}: {
  backup: BackupSummary;
  deviceIp: string;
  deviceName: string | null;
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
            Select which components to restore onto {deviceName || deviceIp}.
            Network components are unchecked by default to avoid losing
            connectivity.
          </DialogDescription>
        </DialogHeader>

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
