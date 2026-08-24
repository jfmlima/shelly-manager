import type { UpdateInfo } from "@/types/api";

export const UPDATE_CHANNELS = ["stable", "beta"] as const;

export type UpdateChannel = (typeof UPDATE_CHANNELS)[number];

export type FirmwareRelease = UpdateInfo & { version: string };

type AvailableUpdates = Record<string, UpdateInfo | undefined>;

export function getChannelRelease(
  availableUpdates: AvailableUpdates | undefined,
  channel: string,
): FirmwareRelease | null {
  const release = availableUpdates?.[channel];
  return isRelease(release) ? release : null;
}

export function getChannelReleases(
  availableUpdates: AvailableUpdates | undefined,
  allowedChannels?: readonly string[],
): { channel: string; release: FirmwareRelease }[] {
  return Object.entries(availableUpdates ?? {}).flatMap(([channel, release]) =>
    isRelease(release) &&
    (!allowedChannels || allowedChannels.includes(channel))
      ? [{ channel, release }]
      : [],
  );
}

export function hasAnyRelease(
  availableUpdates: AvailableUpdates | undefined,
  allowedChannels?: readonly string[],
): boolean {
  return Object.entries(availableUpdates ?? {}).some(
    ([channel, release]) =>
      isRelease(release) &&
      (!allowedChannels || allowedChannels.includes(channel)),
  );
}

function isRelease(
  release: UpdateInfo | undefined,
): release is FirmwareRelease {
  return typeof release?.version === "string" && release.version.length > 0;
}
