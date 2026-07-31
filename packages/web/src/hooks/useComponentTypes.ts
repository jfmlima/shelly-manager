import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { metadataApi } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type { ComponentTypeVocabulary } from "@/lib/schemas/component-types";

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

function forDisplay(types: string[]): string[] {
  const rank = (type: string) => {
    const index = PREFERRED_ORDER.indexOf(type);
    return index === -1 ? PREFERRED_ORDER.length : index;
  };
  return [...types].sort(
    (a, b) => rank(a) - rank(b) || a.localeCompare(b, "en"),
  );
}
