import { useTranslation } from "react-i18next";
import { Card, CardContent } from "@/components/ui/card";

interface FooterProps {
  className?: string;
}

export function Footer({ className }: FooterProps) {
  const { t } = useTranslation();

  return (
    <Card className={className}>
      <CardContent>
        <div className="text-center space-y-2">
          <h3 className="font-semibold">{t("settings.footer.title")}</h3>
          <p className="text-sm text-muted-foreground">
            {t("settings.footer.description")}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
