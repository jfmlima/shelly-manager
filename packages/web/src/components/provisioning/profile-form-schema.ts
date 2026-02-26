import { z } from "zod";

export const profileFormSchema = z.object({
  name: z
    .string()
    .min(1, "Profile name is required")
    .max(100, "Profile name must be 100 characters or fewer"),
  wifi_ssid: z.string().max(32).optional().or(z.literal("")),
  wifi_password: z.string().optional().or(z.literal("")),
  mqtt_enabled: z.boolean(),
  mqtt_server: z.string().optional().or(z.literal("")),
  mqtt_user: z.string().optional().or(z.literal("")),
  mqtt_password: z.string().optional().or(z.literal("")),
  mqtt_topic_prefix_template: z.string().max(300).optional().or(z.literal("")),
  auth_password: z.string().optional().or(z.literal("")),
  device_name_template: z.string().max(100).optional().or(z.literal("")),
  timezone: z.string().optional().or(z.literal("")),
  cloud_enabled: z.boolean(),
  is_default: z.boolean(),
});

export type ProfileFormData = z.infer<typeof profileFormSchema>;

export const defaultProfileFormValues: ProfileFormData = {
  name: "",
  wifi_ssid: "",
  wifi_password: "",
  mqtt_enabled: false,
  mqtt_server: "",
  mqtt_user: "",
  mqtt_password: "",
  mqtt_topic_prefix_template: "",
  auth_password: "",
  device_name_template: "",
  timezone: "",
  cloud_enabled: false,
  is_default: false,
};
