import { z } from "zod";
import { isValidRangeOrCIDR, parseManualIPs } from "@/lib/ip-utils";

export const scanFormSchema = z
  .object({
    scan_mode: z.enum(["mdns", "manual"]),
    manual_mode: z.enum(["ips", "range_cidr"]),
    manual_ips: z.string().optional(),
    range_cidr: z.string().optional(),
    timeout: z.number().min(1).max(300),
    max_workers: z.number().min(1).max(200),
  })
  .refine(
    (data) => {
      if (data.scan_mode === "manual" && data.manual_mode === "range_cidr") {
        return !!data.range_cidr && isValidRangeOrCIDR(data.range_cidr);
      }
      return true;
    },
    {
      message: "Please enter a valid IP range or CIDR notation",
      path: ["range_cidr"],
    },
  )
  .refine(
    (data) => {
      if (data.scan_mode === "manual" && data.manual_mode === "ips") {
        return !!data.manual_ips && parseManualIPs(data.manual_ips).length > 0;
      }
      return true;
    },
    {
      message: "Please enter at least one valid IP address",
      path: ["manual_ips"],
    },
  );

export type ScanFormData = z.infer<typeof scanFormSchema>;
