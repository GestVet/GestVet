import { api } from '../services/api'
import type {
  AddClinicalEntryRequest,
  ClinicalEntryPageResponse,
  ClinicalEntryResponse,
  EntryKind,
} from './types'

export function clinicalEntriesQueryKey(petId: number, kind?: EntryKind) {
  return ['medical-records', petId, kind ?? null] as const
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
