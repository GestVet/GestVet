import { api } from '../services/api'
import type { HospitalizationPageResponse, HospitalizationResponse, NoteResponse } from './types'

export function hospitalizationsQueryKey(petId: number) {
  return ['hospitalizations', petId] as const
}

export async function fetchHospitalizations(petId: number): Promise<HospitalizationPageResponse> {
  const { data } = await api.get<HospitalizationPageResponse>('/hospitalizations', {
    params: { pet_id: petId },
  })
  return data
}

export async function openHospitalization(
  appointmentId: number,
  reason: string,
): Promise<HospitalizationResponse> {
  const { data } = await api.post<HospitalizationResponse>('/hospitalizations', {
    appointment_id: appointmentId,
    reason,
  })
  return data
}

export async function addHospitalizationNote(
  hospitalizationId: number,
  note: string,
): Promise<NoteResponse> {
  const { data } = await api.post<NoteResponse>(
    `/hospitalizations/${String(hospitalizationId)}/notes`,
    { note },
  )
  return data
}

export async function dischargeHospitalization(
  hospitalizationId: number,
  dischargeNotes: string,
): Promise<HospitalizationResponse> {
  const { data } = await api.post<HospitalizationResponse>(
    `/hospitalizations/${String(hospitalizationId)}/discharge`,
    { discharge_notes: dischargeNotes },
  )
  return data
}
