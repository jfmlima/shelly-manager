import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2, Loader2, Save } from "lucide-react";
import { toast } from "sonner";

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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { backupApi, handleApiError } from "@/lib/api";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatTimestamp(ts: number | null): string {
  if (!ts) return "-";
  return new Date(ts * 1000).toLocaleString();
}

export function BackupsTableSection() {
  const queryClient = useQueryClient();
  const {
    data: backups,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["backups", "all"],
    queryFn: () => backupApi.listBackups(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => backupApi.deleteBackup(id),
    onSuccess: () => {
      toast.success("Backup deleted");
      queryClient.invalidateQueries({ queryKey: ["backups"] });
    },
    onError: (err) => toast.error(handleApiError(err)),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Save className="h-5 w-5" />
          <span>Stored Backups</span>
        </CardTitle>
        <CardDescription>
          Every captured snapshot across all devices, newest first.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}
        {error && (
          <p className="text-sm text-destructive">
            Failed to load backups: {handleApiError(error)}
          </p>
        )}
        {backups && backups.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-8">
            No backups stored yet.
          </p>
        )}
        {backups && backups.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Device</TableHead>
                <TableHead>MAC</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {backups.map((backup) => (
                <TableRow key={backup.id}>
                  <TableCell className="font-mono text-xs">
                    {backup.id}
                  </TableCell>
                  <TableCell className="font-medium">
                    {backup.name ||
                      backup.device_name ||
                      backup.device_ip ||
                      "-"}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {backup.device_mac}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        backup.source === "scheduled" ? "secondary" : "outline"
                      }
                    >
                      {backup.source}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatSize(backup.size_bytes)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatTimestamp(backup.created_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      title="Delete"
                      disabled={deleteMutation.isPending}
                      onClick={() => deleteMutation.mutate(backup.id)}
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
    </Card>
  );
}
