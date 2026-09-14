import { z } from 'zod'

import { hoyEnClinica, instanteEnClinica, sumarDias } from '../../services/clinicTime'

// Los mismos limites que aplica el servidor. Repetirlos no duplica la regla:
// avisa antes de gastar un viaje, y el servidor igual los vuelve a exigir.
const MIN_MINUTOS = 15
const MAX_MINUTOS_ATENCION = 12 * 60
const MINUTOS_POR_DIA = 24 * 60
const DIAS_DE_HORIZONTE = 365

export const TIPOS_DE_TURNO = ['regular', 'on_call'] as const
export type TipoDeTurno = (typeof TIPOS_DE_TURNO)[number]

export function limitesDeFecha(): { min: string; max: string } {
  const hoy = hoyEnClinica()
  return { min: hoy, max: sumarDias(hoy, DIAS_DE_HORIZONTE) }
}

/** Un dia de turno: de hoy en adelante y dentro del proximo año. */
export const fechaDeTurno = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Elige el día')
  .refine((dia) => dia >= limitesDeFecha().min, 'Elige hoy o un día que venga')
  .refine((dia) => dia <= limitesDeFecha().max, 'Solo se asignan turnos hasta un año adelante')

export function horaDeTurno(mensaje: string) {
  return z.string().regex(/^\d{2}:\d{2}$/, mensaje)
}

function minutos(hora: string): number {
  const [horas = 0, resto = 0] = hora.split(':').map(Number)
  return horas * 60 + resto
}

function terminaAlDiaSiguiente(desde: string, hasta: string): boolean {
  return minutos(hasta) <= minutos(desde)
}

interface Horario {
  readonly desde: string
  readonly hasta: string
  readonly kind: TipoDeTurno
}

/** Por que un horario no sirve, o `null` si sirve. */
export function problemaDeHorario({ desde, hasta, kind }: Horario): string | null {
  const siguiente = terminaAlDiaSiguiente(desde, hasta)
  if (kind === 'regular' && siguiente) {
    return 'Un turno de atención termina el mismo día. Para cubrir la noche, elige Guardia.'
  }
  const duracion = minutos(hasta) - minutos(desde) + (siguiente ? MINUTOS_POR_DIA : 0)
  if (duracion < MIN_MINUTOS) {
    return 'Un turno dura al menos 15 minutos.'
  }
  if (kind === 'regular' && duracion > MAX_MINUTOS_ATENCION) {
    return 'Un turno de atención dura hasta 12 horas. Divídelo o elige Guardia.'
  }
  return null
}

export const shiftSchema = z
  .object({
    veterinarian_id: z.string().min(1, 'Elige un veterinario'),
    dia: fechaDeTurno,
    desde: horaDeTurno('Elige la hora de inicio'),
    hasta: horaDeTurno('Elige la hora de fin'),
    kind: z.enum(TIPOS_DE_TURNO),
  })
  .superRefine((valores, contexto) => {
    const problema = problemaDeHorario(valores)
    if (problema !== null) {
      contexto.addIssue({ code: 'custom', path: ['hasta'], message: problema })
      return
    }
    if (Date.parse(finDelTurno(valores)) <= Date.now()) {
      contexto.addIssue({
        code: 'custom',
        path: ['hasta'],
        message: 'Ese turno ya terminó. Elige una hora que venga.',
      })
    }
  })

export type ShiftFormValues = z.infer<typeof shiftSchema>

export function turnoVacio(): ShiftFormValues {
  return { veterinarian_id: '', dia: hoyEnClinica(), desde: '09:00', hasta: '18:00', kind: 'regular' }
}

export function inicioDelTurno(valores: Pick<ShiftFormValues, 'dia' | 'desde'>): string {
  return instanteEnClinica(valores.dia, valores.desde)
}

export function finDelTurno(valores: Pick<ShiftFormValues, 'dia' | 'desde' | 'hasta'>): string {
  const dia = terminaAlDiaSiguiente(valores.desde, valores.hasta)
    ? sumarDias(valores.dia, 1)
    : valores.dia
  return instanteEnClinica(dia, valores.hasta)
}
