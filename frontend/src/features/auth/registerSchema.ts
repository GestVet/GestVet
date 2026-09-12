import { z } from 'zod'

// La longitud minima la exige tambien el backend. Repetirla aca no es
// duplicar la regla: es avisar antes de gastar un viaje al servidor.
export const MIN_PASSWORD = 10

export const registerSchema = z.object({
  first_name: z.string().min(1, 'Ingresá tu nombre'),
  last_name: z.string().min(1, 'Ingresá tu apellido'),
  email: z.email('Ingresá un correo válido'),
  phone: z.string().max(32).optional(),
  document_id: z.string().regex(/^\d{8}$/, 'El DNI tiene 8 dígitos'),
  password: z.string().min(MIN_PASSWORD, `Usá al menos ${String(MIN_PASSWORD)} caracteres`),
})

export type RegisterForm = z.infer<typeof registerSchema>
