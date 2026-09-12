import { z } from 'zod'

// La longitud mínima la exige también el backend. Repetirla no duplica la
// regla: avisa antes de gastar un viaje al servidor.
const MIN_PASSWORD = 10

export const staffSchema = z.object({
  first_name: z.string().min(1, 'Ingresá el nombre'),
  last_name: z.string().min(1, 'Ingresá el apellido'),
  email: z.email('Ingresá un correo válido'),
  phone: z.string().max(32).optional(),
  password: z.string().min(MIN_PASSWORD, `Usá al menos ${String(MIN_PASSWORD)} caracteres`),
  role: z.enum(['veterinarian', 'emergency_veterinarian']),
})

export type StaffFormValues = z.infer<typeof staffSchema>

export const EMPTY_STAFF_FORM: StaffFormValues = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  password: '',
  role: 'veterinarian',
}
