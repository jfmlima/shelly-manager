import { useState } from "react";
import {
  CalendarClock,
  Plus,
  Play,
  Pencil,
  Trash2,
  Power,
  Loader2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { toast } from "sonner";
import { handleApiError } from "@/lib/api";
import {
  useBackupSchedules,
  useCreateBackupSchedule,
  useDeleteBackupSchedule,
  useRunBackupSchedule,
  useSetScheduleEnabled,
  useUpdateBackupSchedule,
} from "@/hooks/useBackupSchedules";
import type { BackupSchedule } from "@/types/api";
import { ScheduleForm } from "./schedule-form";
import {
  EMPTY_FORM,
  type ScheduleFormState,
  formToRequest,
  scheduleToForm,
} from "./schedule-form-utils";

function formatInterval(seconds: number): string {
  if (seconds === 3600) return "hourly";
  if (seconds === 86400) return "daily";
  if (seconds === 604800) return "weekly";
  if (seconds % 86400 === 0) return `every ${seconds / 86400}d`;
  if (seconds % 3600 === 0) return `every ${seconds / 3600}h`;
  return `every ${seconds}s`;
}

function formatTargets(schedule: BackupSchedule): string {
  const parts: string[] = [];
  if (schedule.all_credentialed) parts.push("all credentialed");
  if (schedule.target_ips.length)
    parts.push(`${schedule.target_ips.length} IP`);
  if (schedule.target_macs.length)
    parts.push(`${schedule.target_macs.length} MAC`);
  return parts.join(", ") || "-";
}

function formatTimestamp(ts: number | null): string {
  if (!ts) return "-";
  return new Date(ts * 1000).toLocaleString();
}

function statusVariant(
  status: string | null,
): "default" | "secondary" | "destructive" | "outline" {
  if (!status) return "outline";
  if (status.startsWith("ok")) return "default";
  if (status.startsWith("partial")) return "secondary";
  if (status.startsWith("failed")) return "destructive";
  return "outline";
}

export function BackupSchedulesSection() {
  const { data: schedules, isLoading, error } = useBackupSchedules();
  const createMutation = useCreateBackupSchedule();
  const updateMutation = useUpdateBackupSchedule();
  const deleteMutation = useDeleteBackupSchedule();
  const runMutation = useRunBackupSchedule();
  const enabledMutation = useSetScheduleEnabled();

  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<BackupSchedule | null>(null);
  const [form, setForm] = useState<ScheduleFormState>(EMPTY_FORM);

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setCreateOpen(true);
  };

  const openEdit = (schedule: BackupSchedule) => {
    setForm(scheduleToForm(schedule));
    setEditing(schedule);
  };

  const submitCreate = () => {
    const result = formToRequest(form);
    if ("error" in result) {
      toast.error(result.error);
      return;
    }
    createMutation.mutate(result.request, {
      onSuccess: () => setCreateOpen(false),
    });
  };

  const submitEdit = () => {
    if (!editing) return;
    const result = formToRequest(form);
    if ("error" in result) {
      toast.error(result.error);
      return;
    }
    updateMutation.mutate(
      { id: editing.id, data: result.request },
      { onSuccess: () => setEditing(null) },
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <CalendarClock className="h-5 w-5" />
              <span>Backup Schedules</span>
            </CardTitle>
            <CardDescription>
              Automatically back up device configurations on a schedule, with
              optional retention.
            </CardDescription>
          </div>
          <Button size="sm" onClick={openCreate}>
            <Plus className="h-4 w-4 mr-1" /> New Schedule
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}
        {error && (
          <p className="text-sm text-destructive">
            Failed to load schedules: {handleApiError(error)}
          </p>
        )}
        {schedules && schedules.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-8">
            No backup schedules yet.
          </p>
        )}
        {schedules && schedules.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Cadence</TableHead>
                <TableHead>Targets</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Next run</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {schedules.map((schedule) => (
                <TableRow key={schedule.id}>
                  <TableCell className="font-medium">
                    {schedule.name}
                    {!schedule.enabled && (
                      <Badge variant="outline" className="ml-2">
                        disabled
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    {formatInterval(schedule.interval_seconds)}
                  </TableCell>
                  <TableCell>{formatTargets(schedule)}</TableCell>
                  <TableCell>
                    {schedule.last_status ? (
                      <Badge variant={statusVariant(schedule.last_status)}>
                        {schedule.last_status}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">never run</span>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {schedule.enabled
                      ? formatTimestamp(schedule.next_run_at)
                      : "-"}
                  </TableCell>
                  <TableCell className="text-right space-x-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      title="Run now"
                      disabled={runMutation.isPending}
                      onClick={() => runMutation.mutate(schedule.id)}
                    >
                      <Play className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      title={schedule.enabled ? "Disable" : "Enable"}
                      onClick={() =>
                        enabledMutation.mutate({
                          id: schedule.id,
                          enabled: !schedule.enabled,
                        })
                      }
                    >
                      <Power
                        className={
                          schedule.enabled
                            ? "h-4 w-4 text-green-600"
                            : "h-4 w-4 text-muted-foreground"
                        }
                      />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      title="Edit"
                      onClick={() => openEdit(schedule)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      title="Delete"
                      onClick={() => deleteMutation.mutate(schedule.id)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>New Backup Schedule</DialogTitle>
            <DialogDescription>
              Schedules run in the background on the API server.
            </DialogDescription>
          </DialogHeader>
          <ScheduleForm value={form} onChange={setForm} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submitCreate} disabled={createMutation.isPending}>
              {createMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              )}
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={editing !== null}
        onOpenChange={(open) => !open && setEditing(null)}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Backup Schedule</DialogTitle>
            <DialogDescription>
              Changing the cadence restarts the schedule from now.
            </DialogDescription>
          </DialogHeader>
          <ScheduleForm value={form} onChange={setForm} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditing(null)}>
              Cancel
            </Button>
            <Button onClick={submitEdit} disabled={updateMutation.isPending}>
              {updateMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              )}
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
