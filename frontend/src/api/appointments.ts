import { api } from '../services/api'
import type {
  AppointmentPageResponse,
  AppointmentResponse,
  AppointmentTypeListResponse,
  BookAppointmentRequest,
  OpenEmergencyRequest,
} from './types'

export const appointmentsQueryKey = ['appointments'] as const
export const appointmentTypesQueryKey = ['appointments', 'types'] as const

export async function fetchAppointments(): Promise<AppointmentPageResponse> {
  const { data } = await api.get<AppointmentPageResponse>('/appointments')
  return data
}

export async function fetchAppointmentTypes(): Promise<AppointmentTypeListResponse> {
  const { data } = await api.get<AppointmentTypeListResponse>('/appointments/types')
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

export async function confirmAppointment(id: number): Promise<AppointmentResponse> {
  const { data } = await api.post<AppointmentResponse>(`/appointments/${String(id)}/confirm`)
  return data
}

export async function completeAppointment(id: number): Promise<AppointmentResponse> {
  const { data } = await api.post<AppointmentResponse>(`/appointments/${String(id)}/complete`)
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
