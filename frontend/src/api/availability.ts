import { api } from '../services/api'
import type {
  AssignShiftRequest,
  ChangeRequestListResponse,
  ChangeRequestResponse,
  CreateChangeRequest,
  ResolveChangeRequest,
  SlotListResponse,
  SlotResponse,
  WeeklyPlanRequest,
} from './types'

// Las consultas de la agenda cuelgan de una misma raiz: un aviso en tiempo real o un
// turno asignado la invalida entera, y cada pantalla vuelve a pedir lo suyo.
export const availabilityQueryKey = ['availability'] as const
export const mySlotsQueryKey = [...availabilityQueryKey, 'mine'] as const
export const myChangeRequestsQueryKey = [...availabilityQueryKey, 'change-requests', 'mine'] as const

export function rosterQueryKey(lunes: string) {
  return [...availabilityQueryKey, 'roster', lunes] as const
}

export function changeRequestsQueryKey(estado: string) {
  return [...availabilityQueryKey, 'change-requests', 'team', estado] as const
}

export function slotsOfVeterinarianQueryKey(veterinarianId: number) {
  return [...availabilityQueryKey, 'veterinarian', veterinarianId] as const
}

export async function fetchMySlots(
  startsAfter?: string,
  endsBefore?: string,
): Promise<SlotListResponse> {
  const { data } = await api.get<SlotListResponse>('/availability/mine', {
    params: { starts_after: startsAfter, ends_before: endsBefore },
  })
  return data
}

export async function fetchSlotsOfVeterinarian(
  veterinarianId: number,
): Promise<SlotListResponse> {
  const { data } = await api.get<SlotListResponse>('/availability', {
    params: { veterinarian_id: veterinarianId },
  })
  return data
}

export async function fetchRoster(startsAfter: string, endsBefore: string): Promise<SlotListResponse> {
  const { data } = await api.get<SlotListResponse>('/availability/roster', {
    params: { starts_after: startsAfter, ends_before: endsBefore },
  })
  return data
}

export async function assignShift(payload: AssignShiftRequest): Promise<SlotResponse> {
  const { data } = await api.post<SlotResponse>('/availability/shifts', payload)
  return data
}

export async function applyWeeklyPlan(payload: WeeklyPlanRequest): Promise<SlotListResponse> {
  const { data } = await api.post<SlotListResponse>('/availability/weekly-plan', payload)
  return data
}

export async function removeShift(slotId: number): Promise<void> {
  await api.delete(`/availability/shifts/${String(slotId)}`)
}

export async function fetchMyChangeRequests(): Promise<ChangeRequestListResponse> {
  const { data } = await api.get<ChangeRequestListResponse>('/availability/change-requests/mine')
  return data
}

export async function fetchChangeRequests(status?: string): Promise<ChangeRequestListResponse> {
  const { data } = await api.get<ChangeRequestListResponse>('/availability/change-requests', {
    params: { status },
  })
  return data
}

export async function createChangeRequest(
  payload: CreateChangeRequest,
): Promise<ChangeRequestResponse> {
  const { data } = await api.post<ChangeRequestResponse>('/availability/change-requests', payload)
  return data
}

export async function resolveChangeRequest(
  requestId: number,
  payload: ResolveChangeRequest,
): Promise<ChangeRequestResponse> {
  const { data } = await api.post<ChangeRequestResponse>(
    `/availability/change-requests/${String(requestId)}/resolve`,
    payload,
  )
  return data
}
