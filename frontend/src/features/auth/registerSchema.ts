import { z } from 'zod'

import {
  correoRule,
  dniRule,
  MAX_APELLIDO,
  MAX_NOMBRE,
  nombreRule,
  passwordRule,
  telefonoRule,
} from '../../services/fieldRules'

export const registerSchema = z.object({
  first_name: nombreRule('nombre', MAX_NOMBRE),
  last_name: nombreRule('apellido', MAX_APELLIDO),
  email: correoRule,
  phone: telefonoRule,
  document_id: dniRule,
  password: passwordRule,
})

export type RegisterForm = z.infer<typeof registerSchema>
