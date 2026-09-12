import { z } from 'zod'

// La longitud mínima la exige también el backend. Repetirla no duplica la
// regla: avisa antes de gastar un viaje al servidor.
export const MIN_PASSWORD = 10

export const profileSchema = z.object({
  first_name: z.string().min(1, 'Ingresá tu nombre'),
  last_name: z.string().min(1, 'Ingresá tu apellido'),
  phone: z.string().max(32),
  document_id: z.string().regex(/^\d{8}$/, 'El DNI tiene 8 dígitos').or(z.literal('')),
  // Vacía significa "conservar la actual", así que la longitud solo se exige
  // cuando el campo trae algo.
  new_password: z
    .string()
    .min(MIN_PASSWORD, `Usá al menos ${String(MIN_PASSWORD)} caracteres`)
    .or(z.literal('')),
})

export type ProfileForm = z.infer<typeof profileSchema>
