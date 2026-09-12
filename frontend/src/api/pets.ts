import { api } from '../services/api'
import type {
  PetPageResponse,
  PetResponse,
  RegisterPetRequest,
  UpdatePetClinicalProfileRequest,
  UpdatePetOwnerProfileRequest,
} from './types'

export const myPetsQueryKey = ['pets', 'mine'] as const

export function petsOfOwnerQueryKey(ownerId: number) {
  return ['pets', 'owner', ownerId] as const
}

export async function fetchMyPets(): Promise<PetPageResponse> {
  const { data } = await api.get<PetPageResponse>('/pets/mine')
  return data
}

export async function fetchPetsOfOwner(ownerId: number): Promise<PetPageResponse> {
  const { data } = await api.get<PetPageResponse>('/pets', { params: { owner_id: ownerId } })
  return data
}

export async function registerPet(payload: RegisterPetRequest): Promise<PetResponse> {
  const { data } = await api.post<PetResponse>('/pets', payload)
  return data
}

export async function changePetStatus(petId: number, isActive: boolean): Promise<PetResponse> {
  const { data } = await api.patch<PetResponse>(`/pets/${String(petId)}/status`, {
    is_active: isActive,
  })
  return data
}

export async function correctPetStatus(
  petId: number,
  isActive: boolean,
  reason: string,
): Promise<PetResponse> {
  const { data } = await api.patch<PetResponse>(`/pets/${String(petId)}/correct-status`, {
    is_active: isActive,
    reason,
  })
  return data
}

export async function updatePetOwnerProfile(
  petId: number,
  payload: UpdatePetOwnerProfileRequest,
): Promise<PetResponse> {
  const { data } = await api.patch<PetResponse>(`/pets/${String(petId)}/owner-profile`, payload)
  return data
}

export async function updatePetClinicalProfile(
  petId: number,
  payload: UpdatePetClinicalProfileRequest,
): Promise<PetResponse> {
  const { data } = await api.patch<PetResponse>(
    `/pets/${String(petId)}/clinical-profile`,
    payload,
  )
  return data
}
