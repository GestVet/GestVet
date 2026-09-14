import { api } from '../services/api'
import type {
  ActivityPageResponse,
  ClientPageResponse,
  DocumentLookupResponse,
  RegisterStaffRequest,
  RegisterWalkInClientRequest,
  UpdateClientContactRequest,
  UserResponse,
  VeterinarianListResponse,
} from './types'

export const clientsQueryKey = ['clients'] as const
export const staffQueryKey = ['staff'] as const
export const veterinariansQueryKey = ['veterinarians'] as const

export function activityQueryKey(role: string) {
  return ['activity', role] as const
}

export async function fetchActivity(role: string): Promise<ActivityPageResponse> {
  const params = role === '' ? { limit: 100 } : { role, limit: 100 }
  const { data } = await api.get<ActivityPageResponse>('/activity', { params })
  return data
}

export async function fetchVeterinarians(): Promise<VeterinarianListResponse> {
  const { data } = await api.get<VeterinarianListResponse>('/veterinarians')
  return data
}

export async function fetchClients(): Promise<ClientPageResponse> {
  const { data } = await api.get<ClientPageResponse>('/clients')
  return data
}

export async function registerWalkInClient(
  payload: RegisterWalkInClientRequest,
): Promise<UserResponse> {
  const { data } = await api.post<UserResponse>('/clients/walk-in', payload)
  return data
}

export async function updateClientContact(
  clientId: number,
  payload: UpdateClientContactRequest,
): Promise<UserResponse> {
  const { data } = await api.patch<UserResponse>(`/clients/${String(clientId)}/contact`, payload)
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

/** Nombres y apellidos de un DNI, para el alta exprés. El cliente ya lo autorizó. */
export async function lookUpDocument(documentId: string): Promise<DocumentLookupResponse> {
  const { data } = await api.post<DocumentLookupResponse>('/clients/document-lookup', {
    document_id: documentId,
    consent: true,
  })
  return data
}
