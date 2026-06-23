import { BackupSchedulesSection } from "@/components/backup-schedules/schedules-section";
import { BackupsTableSection } from "@/components/backup-schedules/backups-table-section";
import { Footer } from "@/components/ui/footer";

export function BackupSchedules() {
  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col">
      <div className="flex-1 space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Backups</h1>
          <p className="text-muted-foreground">
            Manage automated backup schedules and browse stored snapshots.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <BackupSchedulesSection />
          <BackupsTableSection />
        </div>
      </div>

      <Footer className="mt-6" />
    </div>
  );
}
