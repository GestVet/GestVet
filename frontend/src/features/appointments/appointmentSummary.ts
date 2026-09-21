import type { AppointmentResponse } from '../../api/types'
import { formatearDiaDeInstante, formatearHora } from '../../services/clinicTime'

/** "lunes, 22 de septiembre, 10:00", en la hora de la clínica. */
export function fechaYHora(instante: string): string {
  return `${formatearDiaDeInstante(instante)}, ${formatearHora(instante)}`
}

/** "la cita de Rocco del lunes, 22 de septiembre, 10:00", para una confirmación. */
export function resumenDeCita(cita: AppointmentResponse): string {
  const mascota = cita.pet_name === '' ? '' : ` de ${cita.pet_name}`
  return `la cita${mascota} del ${fechaYHora(cita.scheduled_at)}`
}
