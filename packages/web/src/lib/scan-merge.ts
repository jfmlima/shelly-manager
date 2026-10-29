import type { Device } from "@/types/api";

const FAILED_SCAN_STATUSES = ["unreachable", "error"];

export function isScanFailure(device: Device): boolean {
  return FAILED_SCAN_STATUSES.includes(device.status);
}

/**
 * Fold a scan's results into the known device list.
 *
 * Devices the scan found replace their cached entries. A cached device that
 * the scan covered and did not find stays, flagged not seen; the scan's
 * failure entry for that IP is the proof it was covered. A cached device the
 * scan did not cover is left as it is, so a scan of three addresses does not
 * flag every other known device. An mDNS scan reports no failures, so it only
 * adds and refreshes.
 */
export function mergeScanResults(
  previous: Device[],
  results: Device[],
): Device[] {
  const found = results.filter((device) => !isScanFailure(device));
  const failures = new Map(
    results.filter(isScanFailure).map((device) => [device.ip, device]),
  );
  const foundIps = new Set(found.map((device) => device.ip));

  const kept = previous
    .filter((device) => !foundIps.has(device.ip))
    .map((device) => {
      const failure = failures.get(device.ip);
      if (!failure) {
        return device;
      }
      return {
        ...device,
        not_seen: true,
        not_seen_reason: failure.error_message ?? null,
      };
    });

  return [...found, ...kept];
}
