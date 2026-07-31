import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import { provisioningApi, handleApiError } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type {
  CreateProvisioningProfileRequest,
  UpdateProvisioningProfileRequest,
} from "@/types/api";

export function useProvisioningProfiles() {
  return useQuery({
    queryKey: queryKeys.provisioning.profiles(),
    queryFn: provisioningApi.listProfiles,
  });
}

export function useCreateProvisioningProfile() {
  const { t } = useTranslation();
  const invalidateProfiles = useProfileInvalidation();
  return useMutation({
    mutationFn: (data: CreateProvisioningProfileRequest) =>
      provisioningApi.createProfile(data),
    onSuccess: () => {
      invalidateProfiles();
      toast.success(t("provisioning.profiles.created"));
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useUpdateProvisioningProfile() {
  const { t } = useTranslation();
  const invalidateProfiles = useProfileInvalidation();
  return useMutation({
    mutationFn: (params: {
      id: number;
      data: UpdateProvisioningProfileRequest;
    }) => provisioningApi.updateProfile(params.id, params.data),
    onSuccess: () => {
      invalidateProfiles();
      toast.success(t("provisioning.editDialog.updated"));
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useDeleteProvisioningProfile() {
  const { t } = useTranslation();
  const invalidateProfiles = useProfileInvalidation();
  return useMutation({
    mutationFn: provisioningApi.deleteProfile,
    onSuccess: () => {
      invalidateProfiles();
      toast.success(t("provisioning.profiles.deleted"));
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useSetDefaultProvisioningProfile() {
  const { t } = useTranslation();
  const invalidateProfiles = useProfileInvalidation();
  return useMutation({
    mutationFn: provisioningApi.setDefaultProfile,
    onSuccess: () => {
      invalidateProfiles();
      toast.success(t("provisioning.profiles.defaultUpdated"));
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useDetectDevice() {
  const { t } = useTranslation();
  return useMutation({
    mutationFn: (deviceIp: string) => provisioningApi.detectDevice(deviceIp),
    onSuccess: (info) =>
      toast.success(
        t("provisioning.provision.detect.success", {
          app: info.app || info.model,
          generation: info.generation,
        }),
      ),
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useProvisionDevice() {
  const { t } = useTranslation();
  return useMutation({
    mutationFn: (params: { deviceIp: string; profileId?: number }) =>
      provisioningApi.provisionDevice(params.deviceIp, params.profileId),
    onSuccess: (result) => {
      if (result.success) {
        toast.success(t("provisioning.messages.provisionSuccess"));
      } else {
        toast.error(result.error || t("provisioning.messages.provisionFailed"));
      }
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

export function useVerifyProvision() {
  const { t } = useTranslation();
  return useMutation({
    mutationFn: (params: { deviceMac: string; scanTargets: string[] }) =>
      provisioningApi.verifyProvision(params.deviceMac, params.scanTargets),
    onSuccess: (result) => {
      if (result.found) {
        toast.success(
          t("provisioning.provision.verify.found", { ip: result.device_ip }),
        );
      } else {
        toast.error(t("provisioning.provision.verify.notFound"));
      }
    },
    onError: (error) => toast.error(handleApiError(error)),
  });
}

function useProfileInvalidation() {
  const queryClient = useQueryClient();
  return () =>
    queryClient.invalidateQueries({
      queryKey: queryKeys.provisioning.profiles(),
    });
}
