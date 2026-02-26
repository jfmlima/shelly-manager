import { useTranslation } from "react-i18next";
import type { UseFormReturn } from "react-hook-form";

import { Checkbox } from "@/components/ui/checkbox";
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import type { ProfileFormData } from "./profile-form-schema";

interface ProfileFormFieldsProps {
  form: UseFormReturn<ProfileFormData>;
}

export function ProfileFormFields({ form }: ProfileFormFieldsProps) {
  const { t } = useTranslation();
  const mqttEnabled = form.watch("mqtt_enabled");

  return (
    <div className="grid gap-4 max-h-[60vh] overflow-y-auto pr-2">
      <FormField
        control={form.control}
        name="name"
        render={({ field }) => (
          <FormItem>
            <FormLabel>{t("provisioning.form.profileName")} *</FormLabel>
            <FormControl>
              <Input
                placeholder={t("provisioning.form.profileNamePlaceholder")}
                {...field}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <div className="border-t pt-4">
        <h4 className="font-medium mb-3">
          {t("provisioning.form.wifi.title")}
        </h4>
        <div className="grid gap-3">
          <FormField
            control={form.control}
            name="wifi_ssid"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("provisioning.form.wifi.ssid")}</FormLabel>
                <FormControl>
                  <Input
                    placeholder={t("provisioning.form.wifi.ssidPlaceholder")}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="wifi_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("provisioning.form.wifi.password")}</FormLabel>
                <FormControl>
                  <Input
                    type="password"
                    placeholder={t(
                      "provisioning.form.wifi.passwordPlaceholder",
                    )}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      </div>

      <div className="border-t pt-4">
        <FormField
          control={form.control}
          name="mqtt_enabled"
          render={({ field }) => (
            <FormItem className="flex items-center space-x-2 mb-3">
              <FormControl>
                <Checkbox
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
              <FormLabel className="!mt-0">
                {t("provisioning.form.mqtt.enable")}
              </FormLabel>
            </FormItem>
          )}
        />
        {mqttEnabled && (
          <div className="grid gap-3">
            <FormField
              control={form.control}
              name="mqtt_server"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("provisioning.form.mqtt.server")}</FormLabel>
                  <FormControl>
                    <Input
                      placeholder={t(
                        "provisioning.form.mqtt.serverPlaceholder",
                      )}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="mqtt_user"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      {t("provisioning.form.mqtt.username")}
                    </FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="mqtt_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      {t("provisioning.form.mqtt.password")}
                    </FormLabel>
                    <FormControl>
                      <Input type="password" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="mqtt_topic_prefix_template"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    {t("provisioning.form.mqtt.topicPrefix")}
                  </FormLabel>
                  <FormControl>
                    <Input
                      placeholder={t(
                        "provisioning.form.mqtt.topicPrefixPlaceholder",
                      )}
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    {t("provisioning.form.mqtt.placeholders")}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        )}
      </div>

      <div className="border-t pt-4">
        <h4 className="font-medium mb-3">
          {t("provisioning.form.device.title")}
        </h4>
        <div className="grid gap-3">
          <FormField
            control={form.control}
            name="auth_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  {t("provisioning.form.device.authPassword")}
                </FormLabel>
                <FormControl>
                  <Input
                    type="password"
                    placeholder={t(
                      "provisioning.form.device.authPasswordPlaceholder",
                    )}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="device_name_template"
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  {t("provisioning.form.device.nameTemplate")}
                </FormLabel>
                <FormControl>
                  <Input
                    placeholder={t(
                      "provisioning.form.device.nameTemplatePlaceholder",
                    )}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="timezone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("provisioning.form.device.timezone")}</FormLabel>
                <FormControl>
                  <Input
                    placeholder={t(
                      "provisioning.form.device.timezonePlaceholder",
                    )}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="cloud_enabled"
            render={({ field }) => (
              <FormItem className="flex items-center space-x-2">
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                </FormControl>
                <FormLabel className="!mt-0">
                  {t("provisioning.form.device.cloudEnabled")}
                </FormLabel>
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="is_default"
            render={({ field }) => (
              <FormItem className="flex items-center space-x-2">
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                </FormControl>
                <FormLabel className="!mt-0">
                  {t("provisioning.profiles.setAsDefault")}
                </FormLabel>
              </FormItem>
            )}
          />
        </div>
      </div>
    </div>
  );
}
