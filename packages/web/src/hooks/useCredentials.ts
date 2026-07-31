import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { credentialsApi, handleApiError } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";

export function useCredentials(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: queryKeys.credentials.all(),
    queryFn: credentialsApi.listCredentials,
    enabled: options?.enabled ?? true,
    staleTime: 0,
  });
}

export function useSetCredential() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: credentialsApi.setCredential,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.credentials.all() });
      toast.success(t("common.success"));
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useDeleteCredential() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: credentialsApi.deleteCredential,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.credentials.all() });
      toast.success(t("common.success"));
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}
