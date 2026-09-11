import { api } from '../services/api'
import type {
  ClientPageResponse,
  RegisterStaffRequest,
  UserResponse,
  VeterinarianListResponse,
} from './types'

export const clientsQueryKey = ['clients'] as const
export const staffQueryKey = ['staff'] as const
export const veterinariansQueryKey = ['veterinarians'] as const

export async function fetchVeterinarians(): Promise<VeterinarianListResponse> {
  const { data } = await api.get<VeterinarianListResponse>('/veterinarians')
  return data
}

export async function fetchClients(): Promise<ClientPageResponse> {
  const { data } = await api.get<ClientPageResponse>('/clients')
  return data
}

export async function fetchStaff(): Promise<ClientPageResponse> {
  const { data } = await api.get<ClientPageResponse>('/staff')
  return data
}

export async function registerStaff(payload: RegisterStaffRequest): Promise<UserResponse> {
  const { data } = await api.post<UserResponse>('/staff', payload)
  return data
}

export async function changeUserStatus(
  userId: number,
  isActive: boolean,
): Promise<UserResponse> {
  const { data } = await api.patch<UserResponse>(`/users/${String(userId)}/status`, {
    is_active: isActive,
  })
  return data
}

export async function toggleGuardDuty(userId: number): Promise<UserResponse> {
  const { data } = await api.post<UserResponse>(`/staff/${String(userId)}/guard-duty`)
  return data
}
