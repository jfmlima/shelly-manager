import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Wifi, Plus, Trash2, Star, Loader2, Pencil } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Form } from "@/components/ui/form";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { provisioningApi, handleApiError } from "@/lib/api";
import type {
  CreateProvisioningProfileRequest,
  UpdateProvisioningProfileRequest,
  ProvisioningProfile,
} from "@/types/api";
import { ProfileFormFields } from "./profile-form-fields";
import {
  profileFormSchema,
  defaultProfileFormValues,
  type ProfileFormData,
} from "./profile-form-schema";

function formDataToCreateRequest(
  data: ProfileFormData,
): CreateProvisioningProfileRequest {
  return {
    name: data.name,
    wifi_ssid: data.wifi_ssid || undefined,
    wifi_password: data.wifi_password || undefined,
    mqtt_enabled: data.mqtt_enabled,
    mqtt_server: data.mqtt_server || undefined,
    mqtt_user: data.mqtt_user || undefined,
    mqtt_password: data.mqtt_password || undefined,
    mqtt_topic_prefix_template: data.mqtt_topic_prefix_template || undefined,
    auth_password: data.auth_password || undefined,
    device_name_template: data.device_name_template || undefined,
    timezone: data.timezone || undefined,
    cloud_enabled: data.cloud_enabled,
    is_default: data.is_default,
  };
}

function formDataToUpdateRequest(
  data: ProfileFormData,
): UpdateProvisioningProfileRequest {
  return {
    name: data.name,
    wifi_ssid: data.wifi_ssid || null,
    wifi_password: data.wifi_password || undefined,
    mqtt_enabled: data.mqtt_enabled,
    mqtt_server: data.mqtt_server || null,
    mqtt_user: data.mqtt_user || null,
    mqtt_password: data.mqtt_password || undefined,
    mqtt_topic_prefix_template: data.mqtt_topic_prefix_template || null,
    auth_password: data.auth_password || undefined,
    device_name_template: data.device_name_template || null,
    timezone: data.timezone || null,
    cloud_enabled: data.cloud_enabled,
    is_default: data.is_default,
  };
}

function profileToFormData(profile: ProvisioningProfile): ProfileFormData {
  return {
    name: profile.name,
    wifi_ssid: profile.wifi_ssid || "",
    wifi_password: "",
    mqtt_enabled: profile.mqtt_enabled,
    mqtt_server: profile.mqtt_server || "",
    mqtt_user: profile.mqtt_user || "",
    mqtt_password: "",
    mqtt_topic_prefix_template: profile.mqtt_topic_prefix_template || "",
    auth_password: "",
    device_name_template: profile.device_name_template || "",
    timezone: profile.timezone || "",
    cloud_enabled: profile.cloud_enabled,
    is_default: profile.is_default,
  };
}

export function ProfilesSection() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editingProfile, setEditingProfile] =
    useState<ProvisioningProfile | null>(null);

  const createForm = useForm<ProfileFormData>({
    resolver: zodResolver(profileFormSchema),
    defaultValues: defaultProfileFormValues,
  });

  const editForm = useForm<ProfileFormData>({
    resolver: zodResolver(profileFormSchema),
    defaultValues: defaultProfileFormValues,
  });

  const {
    data: profiles,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["provisioning", "profiles"],
    queryFn: provisioningApi.listProfiles,
    enabled: true,
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateProvisioningProfileRequest) =>
      provisioningApi.createProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["provisioning", "profiles"],
      });
      toast.success(t("provisioning.profiles.created"));
      setCreateOpen(false);
      createForm.reset(defaultProfileFormValues);
    },
    onError: (err) => toast.error(handleApiError(err)),
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: UpdateProvisioningProfileRequest;
    }) => provisioningApi.updateProfile(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["provisioning", "profiles"],
      });
      toast.success(t("provisioning.editDialog.updated"));
      setEditOpen(false);
      setEditingProfile(null);
    },
    onError: (err) => toast.error(handleApiError(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: provisioningApi.deleteProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["provisioning", "profiles"],
      });
      toast.success(t("provisioning.profiles.deleted"));
    },
    onError: (err) => toast.error(handleApiError(err)),
  });

  const setDefaultMutation = useMutation({
    mutationFn: provisioningApi.setDefaultProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["provisioning", "profiles"],
      });
      toast.success(t("provisioning.profiles.defaultUpdated"));
    },
    onError: (err) => toast.error(handleApiError(err)),
  });

  const handleCreate = (data: ProfileFormData) => {
    createMutation.mutate(formDataToCreateRequest(data));
  };

  const handleEdit = (profile: ProvisioningProfile) => {
    setEditingProfile(profile);
    editForm.reset(profileToFormData(profile));
    setEditOpen(true);
  };

  const handleUpdate = (data: ProfileFormData) => {
    if (!editingProfile) return;
    updateMutation.mutate({
      id: editingProfile.id,
      data: formDataToUpdateRequest(data),
    });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Wifi className="h-5 w-5" />
              <span>{t("provisioning.profiles.title")}</span>
            </CardTitle>
            <CardDescription>
              {t("provisioning.profiles.description")}
            </CardDescription>
          </div>
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="h-4 w-4 mr-1" />{" "}
                {t("provisioning.profiles.newProfile")}
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>
                  {t("provisioning.createDialog.title")}
                </DialogTitle>
                <DialogDescription>
                  {t("provisioning.createDialog.description")}
                </DialogDescription>
              </DialogHeader>
              <Form {...createForm}>
                <form onSubmit={createForm.handleSubmit(handleCreate)}>
                  <ProfileFormFields form={createForm} />
                  <DialogFooter className="mt-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setCreateOpen(false)}
                    >
                      {t("common.cancel")}
                    </Button>
                    <Button type="submit" disabled={createMutation.isPending}>
                      {createMutation.isPending && (
                        <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                      )}
                      {t("provisioning.createDialog.create")}
                    </Button>
                  </DialogFooter>
                </form>
              </Form>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}
        {error && (
          <p className="text-sm text-destructive">
            {t("provisioning.profiles.loadFailed", {
              error: handleApiError(error),
            })}
          </p>
        )}
        {profiles && profiles.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-8">
            {t("provisioning.profiles.noProfiles")}
          </p>
        )}
        {profiles && profiles.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("provisioning.profiles.name")}</TableHead>
                <TableHead>{t("provisioning.profiles.wifi")}</TableHead>
                <TableHead>{t("provisioning.profiles.mqtt")}</TableHead>
                <TableHead>{t("provisioning.profiles.auth")}</TableHead>
                <TableHead className="text-right">
                  {t("provisioning.profiles.actions")}
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {profiles.map((profile) => (
                <TableRow key={profile.id}>
                  <TableCell className="font-medium">
                    {profile.name}
                    {profile.is_default && (
                      <Badge variant="secondary" className="ml-2">
                        {t("provisioning.profiles.default")}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>{profile.wifi_ssid || "-"}</TableCell>
                  <TableCell>
                    {profile.mqtt_enabled
                      ? profile.mqtt_server || "enabled"
                      : "-"}
                  </TableCell>
                  <TableCell>
                    {profile.has_auth_password ? (
                      <Badge variant="outline">
                        {t("provisioning.profiles.set")}
                      </Badge>
                    ) : (
                      "-"
                    )}
                  </TableCell>
                  <TableCell className="text-right space-x-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(profile)}
                      title={t("common.edit")}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    {!profile.is_default && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDefaultMutation.mutate(profile.id)}
                        title={t("provisioning.profiles.setAsDefault")}
                      >
                        <Star className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteMutation.mutate(profile.id)}
                      title={t("provisioning.profiles.deleteProfile")}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>

      {/* Edit Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{t("provisioning.editDialog.title")}</DialogTitle>
            <DialogDescription>
              {t("provisioning.editDialog.description")}
            </DialogDescription>
          </DialogHeader>
          <Form {...editForm}>
            <form onSubmit={editForm.handleSubmit(handleUpdate)}>
              <ProfileFormFields form={editForm} />
              <DialogFooter className="mt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setEditOpen(false)}
                >
                  {t("common.cancel")}
                </Button>
                <Button type="submit" disabled={updateMutation.isPending}>
                  {updateMutation.isPending && (
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  )}
                  {t("provisioning.editDialog.save")}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
