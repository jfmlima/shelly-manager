import { z } from "zod";

export const loginFormSchema = z.object({
  token: z.string().min(1, "Token is required"),
  rememberMe: z.boolean(),
});

export type LoginFormData = z.infer<typeof loginFormSchema>;
