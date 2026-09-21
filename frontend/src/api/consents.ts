import { api } from '../services/api'
import type {
  AcceptConsentRequest,
  AcceptEmergencyRiskRequest,
  ConsentKind,
  ConsentListResponse,
  ConsentResponse,
  ConsentStatus,
  ConsentTemplateResponse,
  DeclineConsentRequest,
  RecordInPersonEmergencyRiskRequest,
  RequestConsentRequest,
  WaiveConsentRequest,
} from './types'

export const consentsQueryKey = ['consents'] as const

export function currentTemplateQueryKey(kind: ConsentKind) {
  return [...consentsQueryKey, 'template', kind] as const
}

export function consentQueryKey(id: number) {
  return [...consentsQueryKey, id] as const
}

export function appointmentConsentsQueryKey(appointmentId: number) {
  return [...consentsQueryKey, 'appointment', appointmentId] as const
}

export const myConsentsQueryKey = [...consentsQueryKey, 'mine'] as const

export const myPendingConsentsQueryKey = [...myConsentsQueryKey, 'pending'] as const

export interface ConsentFilters {
  readonly appointment_id?: number
  readonly status?: ConsentStatus
}

export async function fetchCurrentTemplate(kind: ConsentKind): Promise<ConsentTemplateResponse> {
  const { data } = await api.get<ConsentTemplateResponse>('/consents/templates/current', {
    params: { kind },
  })
  return data
}

export async function acceptEmergencyRisk(
  payload: AcceptEmergencyRiskRequest,
): Promise<ConsentResponse> {
  const { data } = await api.post<ConsentResponse>('/consents/emergency-risk', payload)
  return data
}

export async function recordInPersonEmergencyRisk(
  payload: RecordInPersonEmergencyRiskRequest,
): Promise<ConsentResponse> {
  const { data } = await api.post<ConsentResponse>('/consents/emergency-risk/in-person', payload)
  return data
}

export async function fetchConsent(id: number): Promise<ConsentResponse> {
  const { data } = await api.get<ConsentResponse>(`/consents/${String(id)}`)
  return data
}

/** El personal pide los de una cita; el cliente, los suyos (con o sin filtro). */
export async function fetchConsents(filters: ConsentFilters = {}): Promise<ConsentListResponse> {
  const { data } = await api.get<ConsentListResponse>('/consents', { params: filters })
  return data
}

export async function requestConsent(payload: RequestConsentRequest): Promise<ConsentResponse> {
  const { data } = await api.post<ConsentResponse>('/consents', payload)
  return data
}

export async function acceptConsent(
  id: number,
  payload: AcceptConsentRequest,
): Promise<ConsentResponse> {
  const { data } = await api.post<ConsentResponse>(`/consents/${String(id)}/accept`, payload)
  return data
}

export async function declineConsent(
  id: number,
  payload: DeclineConsentRequest,
): Promise<ConsentResponse> {
  const { data } = await api.post<ConsentResponse>(`/consents/${String(id)}/decline`, payload)
  return data
}

export async function acceptConsentInPerson(
  id: number,
  payload: AcceptConsentRequest,
): Promise<ConsentResponse> {
  const { data } = await api.post<ConsentResponse>(
    `/consents/${String(id)}/accept-in-person`,
    payload,
  )
  return data
}

export async function waiveConsent(payload: WaiveConsentRequest): Promise<ConsentResponse> {
  const { data } = await api.post<ConsentResponse>('/consents/waive', payload)
  return data
}
