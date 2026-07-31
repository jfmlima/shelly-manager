import { z } from "zod";

export const componentTypeVocabularySchema = z.object({
  exportable: z.array(z.string()),
  configurable: z.array(z.string()),
  network: z.array(z.string()),
});

export type ComponentTypeVocabulary = z.infer<
  typeof componentTypeVocabularySchema
>;
