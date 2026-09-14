import type { DefaultValues } from 'react-hook-form'
import { z } from 'zod'

import type { VaccineCode } from '../../api/types'
import { textoOpcional } from '../../components/formRules'
import { hoyEnClinica, sumarDias } from '../../services/clinicTime'

const CODIGOS = [
  'rabies',
  'dog_multivalent',
  'dog_kennel_cough',
  'cat_triple',
  'cat_leukemia',
  'deworming',
  'other',
] as const satisfies readonly VaccineCode[]

const FECHA = /^\d{4}-\d{2}-\d{2}$/u

// Los mismos topes que el servidor.
export const vaccinationSchema = z
  .object({
    vaccine: z.enum(CODIGOS, { message: 'Elige la vacuna' }),
    applied_on: z
      .string()
      .regex(FECHA, 'Elige la fecha de aplicación')
      .refine((dia) => dia <= hoyEnClinica(), 'La fecha no puede estar en el futuro'),
    next_due_on: z.string(),
    product_name: textoOpcional(80),
    batch: textoOpcional(40),
    notes: textoOpcional(300),
  })
  .superRefine((valores, contexto) => {
    if (valores.next_due_on !== '' && valores.next_due_on <= valores.applied_on) {
      contexto.addIssue({
        code: 'custom',
        path: ['next_due_on'],
        message: 'Tiene que ser después de la aplicación',
      })
    }
    if (valores.vaccine === 'other' && valores.product_name.trim() === '') {
      contexto.addIssue({
        code: 'custom',
        path: ['product_name'],
        message: 'Para otra vacuna, escribe el nombre del producto',
      })
    }
  })

export type VaccinationFormValues = z.infer<typeof vaccinationSchema>

/** Aplicada hoy y sin vacuna elegida: la próxima dosis se sugiere al elegirla. */
export function vacunaVacia(): DefaultValues<VaccinationFormValues> {
  return { applied_on: hoyEnClinica(), next_due_on: '', product_name: '', batch: '', notes: '' }
}

/** La próxima dosis sugerida, o vacía si la vacuna no lleva refuerzo. */
export function proximaDosis(aplicada: string, intervalo: number | null | undefined): string {
  if (intervalo === null || intervalo === undefined || !FECHA.test(aplicada)) {
    return ''
  }
  return sumarDias(aplicada, intervalo)
}
