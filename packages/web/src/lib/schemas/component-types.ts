import { z } from "zod";

// No defaults: an empty list here would render as a selector offering nothing
// and read as "this device supports no component types" rather than as a
// failed request, so a missing key has to surface as a parse error.
export const componentTypeVocabularySchema = z.object({
  exportable: z.array(z.string()),
  configurable: z.array(z.string()),
  network: z.array(z.string()),
});

export type ComponentTypeVocabulary = z.infer<
  typeof componentTypeVocabularySchema
>;
