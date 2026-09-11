import { api } from '../services/api'
import type {
  AccessTokenResponse,
  LoginRequest,
  RegisterClientRequest,
  UpdateProfileRequest,
  UserResponse,
} from './types'

export const currentUserQueryKey = ['auth', 'me'] as const

export async function login(payload: LoginRequest): Promise<AccessTokenResponse> {
  const { data } = await api.post<AccessTokenResponse>('/auth/login', payload)
  return data
}

export async function registerClient(payload: RegisterClientRequest): Promise<UserResponse> {
  const { data } = await api.post<UserResponse>('/auth/register', payload)
  return data
}

export async function fetchCurrentUser(): Promise<UserResponse> {
  const { data } = await api.get<UserResponse>('/auth/me')
  return data
}

export async function updateProfile(payload: UpdateProfileRequest): Promise<UserResponse> {
  const { data } = await api.patch<UserResponse>('/auth/me', payload)
  return data
}
