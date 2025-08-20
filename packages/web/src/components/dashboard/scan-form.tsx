import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useTranslation } from "react-i18next";
import { useEffect } from "react";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";

// IP address validation regex
const ipRegex =
  /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;

const scanFormSchema = z
  .object({
    start_ip: z.string().optional(),
    end_ip: z.string().optional(),
    use_predefined: z.boolean(),
    timeout: z.number().min(1).max(30),
    max_workers: z.number().min(1).max(100),
  })
  .refine(
    (data) => {
      // If not using predefined, both IP fields are required
      if (!data.use_predefined) {
        return (
          data.start_ip &&
          data.start_ip.trim() !== "" &&
          data.end_ip &&
          data.end_ip.trim() !== ""
        );
      }
      return true;
    },
    {
      message: "Start IP and End IP are required when not using predefined IPs",
      path: ["start_ip"],
    },
  )
  .refine(
    (data) => {
      // Validate start IP format if provided and not using predefined
      if (
        !data.use_predefined &&
        data.start_ip &&
        data.start_ip.trim() !== ""
      ) {
        return ipRegex.test(data.start_ip.trim());
      }
      return true;
    },
    {
      message: "Please enter a valid IP address (e.g., 192.168.1.1)",
      path: ["start_ip"],
    },
  )
  .refine(
    (data) => {
      // Validate end IP format if provided and not using predefined
      if (!data.use_predefined && data.end_ip && data.end_ip.trim() !== "") {
        return ipRegex.test(data.end_ip.trim());
      }
      return true;
    },
    {
      message: "Please enter a valid IP address (e.g., 192.168.1.254)",
      path: ["end_ip"],
    },
  );

export type ScanFormData = z.infer<typeof scanFormSchema>;

interface ScanFormProps {
  onSubmit: (data: ScanFormData) => void;
  isLoading?: boolean;
}

export function ScanForm({ onSubmit, isLoading = false }: ScanFormProps) {
  const { t } = useTranslation();

  const form = useForm<ScanFormData>({
    resolver: zodResolver(scanFormSchema),
    defaultValues: {
      start_ip: "",
      end_ip: "",
      use_predefined: true,
      timeout: 3,
      max_workers: 50,
    },
  });

  const usePredefined = form.watch("use_predefined");

  // Clear IP fields when switching to predefined mode
  useEffect(() => {
    if (usePredefined) {
      form.setValue("start_ip", "");
      form.setValue("end_ip", "");
      // Clear any validation errors
      form.clearErrors(["start_ip", "end_ip"]);
    }
  }, [usePredefined, form]);

  const handleSubmit = (data: ScanFormData) => {
    const cleanData = {
      ...data,
      start_ip: data.start_ip?.trim() || undefined,
      end_ip: data.end_ip?.trim() || undefined,
    };
    onSubmit(cleanData);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Search className="h-5 w-5" />
          <span>{t("dashboard.scanForm.title")}</span>
        </CardTitle>
        <CardDescription>{t("dashboard.scanForm.description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(handleSubmit)}
            className="space-y-4"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="use_predefined"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <div className="flex items-center space-x-2">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                      <FormLabel className="text-sm font-normal">
                        {t("dashboard.scanForm.usePredefined")}
                      </FormLabel>
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {!usePredefined && (
                <>
                  <FormField
                    control={form.control}
                    name="start_ip"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          {t("dashboard.scanForm.startIp")}
                          {!usePredefined && (
                            <span className="text-red-500 ml-1">*</span>
                          )}
                        </FormLabel>
                        <FormControl>
                          <Input
                            placeholder="192.168.1.1"
                            {...field}
                            value={field.value || ""}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="end_ip"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          {t("dashboard.scanForm.endIp")}
                          {!usePredefined && (
                            <span className="text-red-500 ml-1">*</span>
                          )}
                        </FormLabel>
                        <FormControl>
                          <Input
                            placeholder="192.168.1.254"
                            {...field}
                            value={field.value || ""}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </>
              )}

              <FormField
                control={form.control}
                name="timeout"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("dashboard.scanForm.timeout")}</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min="1"
                        max="30"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="max_workers"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("dashboard.scanForm.maxWorkers")}</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min="1"
                        max="100"
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full md:w-auto"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2" />
                  {t("dashboard.scanForm.scanning")}
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  {t("dashboard.scanForm.scanButton")}
                </>
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
