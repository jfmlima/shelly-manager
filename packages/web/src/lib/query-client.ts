import { QueryClient } from "@tanstack/react-query";
import { createAsyncStoragePersister } from "@tanstack/query-async-storage-persister";

export const persister = createAsyncStoragePersister({
  storage: window.localStorage,
  key: "shelly-query-cache",
  throttleTime: 1000,
  serialize: JSON.stringify,
  deserialize: (data: string) => {
    try {
      return JSON.parse(data);
    } catch {
      return null;
    }
  },
});

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000,
      gcTime: 1000 * 60 * 60 * 24, // 24 hours for persistence
      enabled: false,
    },
    mutations: {
      retry: 1,
    },
  },
});
