import { z } from 'zod'

import { fechaDeNacimientoRule, microchipRule, textoOpcional } from './formRules'

export const MAX_COLOR = 80
export const MAX_TEMPERAMENTO = 120

export const petOwnerProfileSchema = z.object({
  species: z.string().min(1, 'Elige la especie'),
  breed: z.string().min(1, 'Elige la raza'),
  birth_date: fechaDeNacimientoRule,
  sex: z.enum(['', 'male', 'female']),
  color: textoOpcional(MAX_COLOR),
  microchip_number: microchipRule,
  temperament: textoOpcional(MAX_TEMPERAMENTO),
})

export type PetOwnerProfileValues = z.infer<typeof petOwnerProfileSchema>
