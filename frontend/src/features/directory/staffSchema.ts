import { z } from 'zod'

import {
  correoRule,
  MAX_APELLIDO,
  MAX_NOMBRE,
  nombreRule,
  passwordRule,
  telefonoRule,
} from '../../services/fieldRules'

export const staffSchema = z.object({
  first_name: nombreRule('nombre', MAX_NOMBRE, 'el'),
  last_name: nombreRule('apellido', MAX_APELLIDO, 'el'),
  email: correoRule,
  phone: telefonoRule,
  password: passwordRule,
  // El alta de personal solo crea veterinarios: la guardia es un turno, no un rol.
  role: z.literal('veterinarian'),
  // Con qué atiende: al menos una, para que aparezca en el filtro de
  // especialidad al reservar.
  specialty_ids: z.array(z.number()).min(1, 'Elige al menos una especialidad.'),
})

export type StaffFormValues = z.infer<typeof staffSchema>

export const EMPTY_STAFF_FORM: StaffFormValues = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  password: '',
  role: 'veterinarian',
  specialty_ids: [],
}
