import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { metadataApi } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type { ComponentTypeVocabulary } from "@/lib/schemas/component-types";

// The list the web hardcoded for both dialogs before the API served this
// vocabulary. It survives for two jobs, neither of which is deciding what a
// user may pick: the order the selectors read in, and the bridge for the
// render before the query resolves.
const PREFERRED_ORDER = [
  "switch",
  "input",
  "cover",
  "sys",
  "cloud",
  "wifi",
  "ble",
  "mqtt",
  "ws",
  "script",
  "knx",
  "modbus",
  "zigbee",
];

const FALLBACK_VOCABULARY: ComponentTypeVocabulary = {
  exportable: PREFERRED_ORDER,
  configurable: PREFERRED_ORDER,
  network: ["wifi", "eth", "mqtt", "ws", "cloud"],
};

export function useComponentTypes() {
  const query = useQuery({
    queryKey: queryKeys.metadata.componentTypes(),
    queryFn: metadataApi.getComponentTypes,
    // The vocabulary moves only when the API is redeployed. Long rather than
    // infinite so a tab left open across a deploy picks the new one up on the
    // next dialog open instead of holding the old list until a reload.
    staleTime: 60 * 60 * 1000,
  });

  const vocabulary = query.data ?? FALLBACK_VOCABULARY;

  const componentTypes = useMemo(
    () => ({
      exportable: forDisplay(vocabulary.exportable),
      configurable: forDisplay(vocabulary.configurable),
      network: vocabulary.network,
    }),
    [vocabulary],
  );

  return { ...query, componentTypes };
}

// The API sorts alphabetically so its own output stays stable, which buries
// switch below two dozen types most devices do not have. Ordering is the
// selector's problem, so the everyday types lead and the rest follow
// alphabetically behind them.
function forDisplay(types: string[]): string[] {
  const rank = (type: string) => {
    const index = PREFERRED_ORDER.indexOf(type);
    return index === -1 ? PREFERRED_ORDER.length : index;
  };
  return [...types].sort(
    (a, b) => rank(a) - rank(b) || a.localeCompare(b, "en"),
  );
}
