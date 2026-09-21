import type { AppointmentResponse } from '../../api/types'
import { formatearDiaDeInstante, formatearHora } from '../../services/clinicTime'

/** "la cita del lunes 22 de septiembre a las 10:00", para una confirmación. */
export function resumenDeCita(cita: AppointmentResponse): string {
  const cuando = `${formatearDiaDeInstante(cita.scheduled_at)} a las ${formatearHora(cita.scheduled_at)}`
  return `la cita del ${cuando}`
}

/** La hora desde la que se habilita una acción, en la hora de la clínica. */
export function horaDeHabilitacion(instante: string): string {
  return `${formatearDiaDeInstante(instante)}, ${formatearHora(instante)}`
}
