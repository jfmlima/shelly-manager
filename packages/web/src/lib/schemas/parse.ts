import type { z } from "zod";

export function parseResponse<T>(
  schema: z.ZodType<T>,
  data: unknown,
  source: string,
): T {
  const result = schema.safeParse(data);
  if (result.success) {
    return result.data;
  }
  throw new Error(
    `Unexpected response from ${source}: ${describe(result.error)}`,
  );
}

function describe(error: z.ZodError): string {
  return error.issues
    .slice(0, 3)
    .map((issue) => {
      const path = issue.path.join(".");
      return path ? `${path}: ${issue.message}` : issue.message;
    })
    .join("; ");
}
