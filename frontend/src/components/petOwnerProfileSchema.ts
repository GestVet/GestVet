import { z } from 'zod'

import { decimalRule, fechaDeNacimientoRule, microchipRule, textoOpcional } from './formRules'

export const MAX_COLOR = 80
export const MAX_TEMPERAMENTO = 120

function esquemaDeFicha(microchipGuardado: string) {
  return z.object({
  species: z.string().min(1, 'Elige la especie'),
  breed: z.string().min(1, 'Elige la raza'),
  birth_date: fechaDeNacimientoRule,
  sex: z.enum(['', 'male', 'female']),
  color: textoOpcional(MAX_COLOR),
  microchip_number: microchipRule(microchipGuardado),
  temperament: textoOpcional(MAX_TEMPERAMENTO),
  // Los mismos topes que el servidor: 120 kg y 200 cm cubren de un hámster a un gran danés.
  weight_kg: decimalRule({ max: 120, decimales: 2, unidad: 'kg' }),
  height_cm: decimalRule({ max: 200, decimales: 1, unidad: 'cm' }),
  is_sterilized: z.enum(['', 'true', 'false']),
  allergies: textoOpcional(300),
  })
}

/** La ficha del dueño; el microchip ya guardado se acepta aunque no sea ISO. */
export function petOwnerProfileSchemaFor(microchipGuardado: string) {
  return esquemaDeFicha(microchipGuardado)
}

export type PetOwnerProfileValues = z.infer<ReturnType<typeof esquemaDeFicha>>
