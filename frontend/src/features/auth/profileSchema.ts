import { z } from 'zod'

import {
  dniRule,
  MAX_APELLIDO,
  MAX_NOMBRE,
  nombreRule,
  passwordRule,
  telefonoRule,
} from '../../services/fieldRules'

export const profileSchema = z.object({
  first_name: nombreRule('nombre', MAX_NOMBRE),
  last_name: nombreRule('apellido', MAX_APELLIDO),
  phone: telefonoRule,
  // El perfil de una cuenta creada por la clinica puede no tener DNI todavia.
  document_id: dniRule.or(z.literal('')),
  // Vacía significa "conservar la actual", así que la longitud solo se exige
  // cuando el campo trae algo.
  new_password: passwordRule.or(z.literal('')),
})

export type ProfileForm = z.infer<typeof profileSchema>
