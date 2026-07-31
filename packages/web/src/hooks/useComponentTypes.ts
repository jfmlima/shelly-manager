import { useQuery } from "@tanstack/react-query";

import { metadataApi } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type { ComponentTypeVocabulary } from "@/lib/schemas/component-types";

// The single list the web hardcoded for both dialogs before the API served
// this vocabulary. It covers only the types that shipped first, so it is a
// bridge for the render before the query resolves, never the answer: the API
// is the source of truth and knows about types this list never heard of.
const TYPES_THE_WEB_ONCE_HARDCODED = [
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
  exportable: TYPES_THE_WEB_ONCE_HARDCODED,
  configurable: TYPES_THE_WEB_ONCE_HARDCODED,
  network: ["wifi", "eth", "mqtt", "ws", "cloud"],
};

export function useComponentTypes() {
  const query = useQuery({
    queryKey: queryKeys.metadata.componentTypes(),
    queryFn: metadataApi.getComponentTypes,
    // The vocabulary moves only when the API is redeployed, so refetching it
    // per dialog open buys a request for an answer that cannot have changed.
    staleTime: Infinity,
    gcTime: Infinity,
  });

  return {
    ...query,
    componentTypes: query.data ?? FALLBACK_VOCABULARY,
  };
}
