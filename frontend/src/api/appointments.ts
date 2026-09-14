import { api } from '../services/api'
import type {
  AppointmentPageResponse,
  AppointmentResponse,
  AppointmentStatus,
  AppointmentTypeListResponse,
  BookAppointmentRequest,
  OpenEmergencyRequest,
  OpenTimesResponse,
  OpenWalkInEmergencyRequest,
} from './types'

export interface AppointmentsFilter {
  readonly status?: AppointmentStatus
  readonly is_emergency?: boolean
  readonly starts_after?: string
  readonly ends_before?: string
}

export const appointmentsQueryKey = ['appointments'] as const
export const appointmentTypesQueryKey = ['appointments', 'types'] as const

export function appointmentsFilterQueryKey(filter: AppointmentsFilter) {
  return [...appointmentsQueryKey, filter] as const
}

export async function fetchAppointments(
  filter: AppointmentsFilter = {},
): Promise<AppointmentPageResponse> {
  const { data } = await api.get<AppointmentPageResponse>('/appointments', { params: filter })
  return data
}

export async function fetchAppointmentTypes(): Promise<AppointmentTypeListResponse> {
  const { data } = await api.get<AppointmentTypeListResponse>('/appointments/types')
  return data
}

// Cuelga de la clave de citas a proposito: cualquier cambio en una cita, propio
// o avisado en tiempo real, vuelve a calcular las horas libres.
export function openTimesQueryKey(appointmentTypeId: number, fromDate: string, days: number) {
  return [...appointmentsQueryKey, 'open-times', appointmentTypeId, fromDate, days] as const
}

export async function fetchOpenTimes(
  appointmentTypeId: number,
  fromDate: string,
  days: number,
): Promise<OpenTimesResponse> {
  const { data } = await api.get<OpenTimesResponse>('/appointments/open-times', {
    params: { appointment_type_id: appointmentTypeId, from_date: fromDate, days },
  })
  return data
}

export async function bookAppointment(
  payload: BookAppointmentRequest,
): Promise<AppointmentResponse> {
  const { data } = await api.post<AppointmentResponse>('/appointments', payload)
  return data
}

export async function openEmergency(
  payload: OpenEmergencyRequest,
): Promise<AppointmentResponse> {
  const { data } = await api.post<AppointmentResponse>('/appointments/emergency', payload)
  return data
}

export async function openWalkInEmergency(
  payload: OpenWalkInEmergencyRequest,
): Promise<AppointmentResponse> {
  const { data } = await api.post<AppointmentResponse>('/appointments/emergency/walk-in', payload)
  return data
}

export async function confirmAppointment(id: number): Promise<AppointmentResponse> {
  const { data } = await api.post<AppointmentResponse>(`/appointments/${String(id)}/confirm`)
  return data
}

export async function completeAppointment(id: number): Promise<AppointmentResponse> {
  const { data } = await api.post<AppointmentResponse>(`/appointments/${String(id)}/complete`)
  return data
}

export async function markAppointmentNoShow(id: number): Promise<AppointmentResponse> {
  const { data } = await api.post<AppointmentResponse>(`/appointments/${String(id)}/no-show`)
  return data
}

export async function cancelAppointment(
  id: number,
  reason: string,
): Promise<AppointmentResponse> {
  const { data } = await api.post<AppointmentResponse>(`/appointments/${String(id)}/cancel`, {
    reason,
  })
  return data
}
