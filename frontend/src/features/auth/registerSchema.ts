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
  accepts_identity_check: z
    .boolean()
    .refine((autorizado) => autorizado, 'Necesitamos tu autorización para verificar tu DNI'),
  accepts_terms: z
    .boolean()
    .refine((aceptados) => aceptados, 'Debes aceptar los términos y condiciones'),
})

export type RegisterForm = z.infer<typeof registerSchema>
