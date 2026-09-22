import { z } from 'zod'

// Los mismos límites que el servidor.
const MIN_JUSTIFICACION = 20
export const MAX_JUSTIFICACION = 1000

export const waiveConsentSchema = z.object({
  kind: z.string().min(1, 'Elige qué consentimiento no se pudo pedir'),
  justification: z
    .string()
    .trim()
    .min(
      MIN_JUSTIFICACION,
      `Explica qué le pasaba a la mascota y por qué no se ubicó al responsable (al menos ${String(MIN_JUSTIFICACION)} caracteres)`,
    )
    .max(MAX_JUSTIFICACION, `Usa como máximo ${String(MAX_JUSTIFICACION)} caracteres`),
})

export type WaiveConsentInput = z.infer<typeof waiveConsentSchema>
