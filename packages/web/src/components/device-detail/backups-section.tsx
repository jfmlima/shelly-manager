import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
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
import { backupApi } from "@/lib/api";
import {
  useBackups,
  useCreateBackup,
  useDeleteBackup,
  useRestoreBackup,
} from "@/hooks/useBackups";
import type { BackupSummary } from "@/types/api";

const NETWORK_TYPES = new Set(["wifi", "eth", "mqtt", "ws", "cloud"]);

interface BackupsSectionProps {
  deviceIp: string;
  deviceMac: string | null;
  deviceName: string | null;
}

interface SnapshotComponent {
  type?: string;
}

export function BackupsSection({
  deviceIp,
  deviceMac,
  deviceName,
}: BackupsSectionProps) {
  const { data: backups, isLoading } = useBackups(deviceMac);
  const createBackup = useCreateBackup(deviceMac);
  const [restoreTarget, setRestoreTarget] = useState<BackupSummary | null>(null);

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
          onClick={() =>
            createBackup.mutate({ deviceIp, name: undefined })
          }
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
        ) : !backups || backups.length === 0 ? (
          <p className="text-sm text-muted-foreground">No backups yet.</p>
        ) : (
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
              {backups.map((backup) => (
                <BackupRow
                  key={backup.id}
                  backup={backup}
                  deviceMac={deviceMac}
                  formatDate={formatDate}
                  onRestore={() => setRestoreTarget(backup)}
                />
              ))}
            </TableBody>
          </Table>
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
  deviceMac,
  formatDate,
  onRestore,
}: {
  backup: BackupSummary;
  deviceMac: string | null;
  formatDate: (ts: number | null) => string;
  onRestore: () => void;
}) {
  const deleteBackup = useDeleteBackup(deviceMac);
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
  const { data: detail, isLoading } = useQuery({
    queryKey: ["backup", backup.id],
    queryFn: () => backupApi.getBackup(backup.id),
  });

  const componentTypes = useMemo(() => {
    const components = (detail?.snapshot?.components ?? {}) as Record<
      string,
      SnapshotComponent
    >;
    return Object.entries(components).map(([key, value]) => ({
      key,
      type: value?.type ?? "",
      network: NETWORK_TYPES.has(value?.type ?? ""),
    }));
  }, [detail]);

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

        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading components...</p>
        ) : (
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
                      network — may disconnect
                    </span>
                  )}
                </Label>
              </div>
            ))}
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
