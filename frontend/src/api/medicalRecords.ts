import { api } from '../services/api'
import type {
  AddClinicalEntryRequest,
  ClinicalSummaryResponse,
  PublicVaccinationCardResponse,
  ClinicalEntryPageResponse,
  ClinicalEntryResponse,
  EntryKind,
  RecordVaccinationRequest,
  VaccinationCardResponse,
  VaccinationResponse,
  VaccineOptionListResponse,
} from './types'

// Todas las consultas de una mascota cuelgan de esta clave.
const MEDICAL_RECORDS = 'medical-records'

export function clinicalEntriesQueryKey(petId: number, kind?: EntryKind) {
  return [MEDICAL_RECORDS, petId, kind ?? null] as const
}

export async function fetchClinicalEntries(
  petId: number,
  kind?: EntryKind,
): Promise<ClinicalEntryPageResponse> {
  const { data } = await api.get<ClinicalEntryPageResponse>('/medical-records', {
    params: { pet_id: petId, kind },
  })
  return data
}

export async function addClinicalEntry(
  payload: AddClinicalEntryRequest,
): Promise<ClinicalEntryResponse> {
  const { data } = await api.post<ClinicalEntryResponse>('/medical-records', payload)
  return data
}

export async function downloadClinicalHistoryReport(petId: number): Promise<Blob> {
  const { data } = await api.get<Blob>('/medical-records/report', {
    params: { pet_id: petId },
    responseType: 'blob',
  })
  return data
}

// Debajo de la mascota: invalidar su historia refresca también el carnet.
export function vaccinationCardQueryKey(petId: number) {
  return [MEDICAL_RECORDS, petId, 'vaccinations'] as const
}

export function vaccineOptionsQueryKey(petId: number) {
  return [MEDICAL_RECORDS, petId, 'vaccine-options'] as const
}

export async function fetchVaccinationCard(petId: number): Promise<VaccinationCardResponse> {
  const { data } = await api.get<VaccinationCardResponse>('/medical-records/vaccinations', {
    params: { pet_id: petId },
  })
  return data
}

export async function fetchVaccineOptions(petId: number): Promise<VaccineOptionListResponse> {
  const { data } = await api.get<VaccineOptionListResponse>(
    '/medical-records/vaccinations/options',
    { params: { pet_id: petId } },
  )
  return data
}

export async function recordVaccination(
  payload: RecordVaccinationRequest,
): Promise<VaccinationResponse> {
  const { data } = await api.post<VaccinationResponse>('/medical-records/vaccinations', payload)
  return data
}

// Un modelo tarda más que una consulta a la base: se le da más margen.
const TIEMPO_DEL_ASISTENTE_MS = 60_000

export async function summarizeClinicalHistory(petId: number): Promise<ClinicalSummaryResponse> {
  const { data } = await api.post<ClinicalSummaryResponse>(
    '/medical-records/assistant/summary',
    { pet_id: petId },
    { timeout: TIEMPO_DEL_ASISTENTE_MS },
  )
  return data
}

export async function downloadVaccinationCardPdf(petId: number): Promise<Blob> {
  const { data } = await api.get<Blob>('/medical-records/vaccinations/card.pdf', {
    params: { pet_id: petId },
    responseType: 'blob',
  })
  return data
}

export function publicVaccinationCardQueryKey(token: string) {
  return ['public-vaccination-card', token] as const
}

/** La verificación que abre el QR del carnet. No necesita sesión. */
export async function fetchPublicVaccinationCard(
  token: string,
): Promise<PublicVaccinationCardResponse> {
  const { data } = await api.get<PublicVaccinationCardResponse>(
    `/public/vaccination-cards/${encodeURIComponent(token)}`,
  )
  return data
}
