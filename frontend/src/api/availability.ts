import { api } from '../services/api'
import type { PublishSlotRequest, SlotListResponse, SlotResponse } from './types'

export const mySlotsQueryKey = ['availability', 'mine'] as const

export function slotsOfVeterinarianQueryKey(veterinarianId: number) {
  return ['availability', veterinarianId] as const
}

export async function fetchMySlots(): Promise<SlotListResponse> {
  const { data } = await api.get<SlotListResponse>('/availability/mine')
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

export async function publishSlot(payload: PublishSlotRequest): Promise<SlotResponse> {
  const { data } = await api.post<SlotResponse>('/availability', payload)
  return data
}

export async function withdrawSlot(slotId: number): Promise<void> {
  await api.delete(`/availability/${String(slotId)}`)
}
