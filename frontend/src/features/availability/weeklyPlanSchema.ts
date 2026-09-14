import { z } from 'zod'

import { hoyEnClinica, lunesDe, sumarDias } from '../../services/clinicTime'
import { fechaDeTurno, horaDeTurno, problemaDeHorario, TIPOS_DE_TURNO } from './shiftSchema'

export const MAX_SEMANAS = 12
export const NOMBRES_DE_DIAS = [
  'Lunes',
  'Martes',
  'Miércoles',
  'Jueves',
  'Viernes',
  'Sábado',
  'Domingo',
] as const

export const weeklyPlanSchema = z
  .object({
    veterinarian_id: z.string().min(1, 'Elige un veterinario'),
    first_day: fechaDeTurno,
    weeks: z.string().regex(/^(?:[1-9]|1[0-2])$/, `Elige de 1 a ${String(MAX_SEMANAS)} semanas`),
    weekdays: z.array(z.number().int().min(0).max(6)).min(1, 'Elige al menos un día'),
    desde: horaDeTurno('Elige la hora de inicio'),
    hasta: horaDeTurno('Elige la hora de fin'),
    kind: z.enum(TIPOS_DE_TURNO),
  })
  .superRefine((valores, contexto) => {
    const problema = problemaDeHorario(valores)
    if (problema !== null) {
      contexto.addIssue({ code: 'custom', path: ['hasta'], message: problema })
    }
  })

export type WeeklyPlanFormValues = z.infer<typeof weeklyPlanSchema>

/** Desde el lunes que viene, de lunes a viernes, un mes. */
export function horarioVacio(): WeeklyPlanFormValues {
  return {
    veterinarian_id: '',
    first_day: sumarDias(lunesDe(hoyEnClinica()), 7),
    weeks: '4',
    weekdays: [0, 1, 2, 3, 4],
    desde: '09:00',
    hasta: '18:00',
    kind: 'regular',
  }
}
