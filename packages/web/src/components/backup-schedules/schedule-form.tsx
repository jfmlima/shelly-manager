import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Cadence, ScheduleFormState } from "./schedule-form-utils";

interface ScheduleFormProps {
  value: ScheduleFormState;
  onChange: (next: ScheduleFormState) => void;
}

export function ScheduleForm({ value, onChange }: ScheduleFormProps) {
  const set = <K extends keyof ScheduleFormState>(
    key: K,
    fieldValue: ScheduleFormState[K],
  ) => onChange({ ...value, [key]: fieldValue });

  return (
    <div className="space-y-4 py-2">
      <div className="space-y-1.5">
        <Label htmlFor="schedule-name">Name</Label>
        <Input
          id="schedule-name"
          value={value.name}
          onChange={(e) => set("name", e.target.value)}
          placeholder="nightly-backup"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label>Cadence</Label>
          <Select
            value={value.cadence}
            onValueChange={(v) => set("cadence", v as Cadence)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="hourly">Hourly</SelectItem>
              <SelectItem value="daily">Daily</SelectItem>
              <SelectItem value="weekly">Weekly</SelectItem>
              <SelectItem value="custom">Custom</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {value.cadence === "custom" && (
          <div className="space-y-1.5">
            <Label htmlFor="schedule-interval">Interval (seconds)</Label>
            <Input
              id="schedule-interval"
              type="number"
              min={60}
              value={value.intervalSeconds}
              onChange={(e) => set("intervalSeconds", e.target.value)}
            />
          </div>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="schedule-ips">Target IPs</Label>
        <Input
          id="schedule-ips"
          value={value.targetIps}
          onChange={(e) => set("targetIps", e.target.value)}
          placeholder="192.168.1.10, 192.168.1.0/24"
        />
        <p className="text-xs text-muted-foreground">
          Comma or space separated. IPs, ranges, or CIDR. Ranges and CIDR are
          scanned for live devices at run time.
        </p>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="schedule-macs">Target MACs</Label>
        <Input
          id="schedule-macs"
          value={value.targetMacs}
          onChange={(e) => set("targetMacs", e.target.value)}
          placeholder="AABBCCDDEEFF"
        />
        <p className="text-xs text-muted-foreground">
          Resolved to an IP via the device's last-seen address.
        </p>
      </div>

      <div className="flex items-center space-x-2">
        <Checkbox
          id="schedule-all"
          checked={value.allCredentialed}
          onCheckedChange={(checked) =>
            set("allCredentialed", checked === true)
          }
        />
        <Label htmlFor="schedule-all" className="font-normal">
          Back up every device with stored credentials
        </Label>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="schedule-keep">Keep last N</Label>
          <Input
            id="schedule-keep"
            type="number"
            min={1}
            value={value.keepLast}
            onChange={(e) => set("keepLast", e.target.value)}
            placeholder="optional"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="schedule-age">Max age (days)</Label>
          <Input
            id="schedule-age"
            type="number"
            min={1}
            value={value.maxAgeDays}
            onChange={(e) => set("maxAgeDays", e.target.value)}
            placeholder="optional"
          />
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <Checkbox
          id="schedule-enabled"
          checked={value.enabled}
          onCheckedChange={(checked) => set("enabled", checked === true)}
        />
        <Label htmlFor="schedule-enabled" className="font-normal">
          Enabled
        </Label>
      </div>
    </div>
  );
}
