import { z } from 'zod'

import { textoOpcional } from '../../components/formRules'
import { firmaRule } from '../../services/fieldRules'

// El mismo tope que el servidor para la descripción de una cita.
const MAX_DESCRIPCION = 500

export const emergencySchema = z.object({
  pet_id: z.string().min(1, 'Elige la mascota'),
  description: textoOpcional(MAX_DESCRIPCION),
  accepted: z.boolean().refine((marcado) => marcado, 'Marca la casilla para aceptar el riesgo'),
  signer_name: firmaRule,
})

export type EmergencyFormInput = z.input<typeof emergencySchema>
export type EmergencyFormValues = z.output<typeof emergencySchema>
