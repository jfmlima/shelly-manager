import { useTranslation } from "react-i18next";

import {
  ProfilesSection,
  ProvisionDeviceSection,
} from "@/components/provisioning";
import { Footer } from "@/components/ui/footer";

export function Provisioning() {
  const { t } = useTranslation();

  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col">
      <div className="flex-1 space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {t("provisioning.title")}
          </h1>
          <p className="text-muted-foreground">{t("provisioning.subtitle")}</p>
        </div>

        <div className="grid grid-cols-1 gap-6">
          <ProvisionDeviceSection />
          <ProfilesSection />
        </div>
      </div>

      <Footer className="mt-6" />
    </div>
  );
}
