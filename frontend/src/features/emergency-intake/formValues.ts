import { z } from 'zod'

import { nombreDeMascotaRule, textoOpcional } from '../../components/formRules'
import {
  dniRule,
  firmaRule,
  MAX_APELLIDO,
  MAX_NOMBRE,
  nombreRule,
  telefonoRule,
} from '../../services/fieldRules'

export const MAX_MOTIVO = 500

export const walkInEmergencySchema = z.object({
  first_name: nombreRule('nombre', MAX_NOMBRE, 'el'),
  last_name: nombreRule('apellido', MAX_APELLIDO, 'el'),
  document_id: dniRule,
  phone: telefonoRule,
  pet_name: nombreDeMascotaRule,
  pet_species: z.string().min(1, 'Elige la especie'),
  description: textoOpcional(MAX_MOTIVO),
  risk_accepted: z
    .boolean()
    .refine((marcado) => marcado, 'Marca la casilla cuando el responsable haya aceptado'),
  signer_name: firmaRule,
})

export type WalkInEmergencyFormValues = z.infer<typeof walkInEmergencySchema>

export const EMPTY_WALK_IN_EMERGENCY: WalkInEmergencyFormValues = {
  first_name: '',
  last_name: '',
  document_id: '',
  phone: '',
  pet_name: '',
  pet_species: '',
  description: '',
  risk_accepted: false,
  signer_name: '',
}
