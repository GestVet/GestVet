import { api } from '../services/api'
import type {
  AccessTokenResponse,
  ForgotPasswordRequest,
  LoginRequest,
  MessageResponse,
  RegisterClientRequest,
  ResetPasswordRequest,
  UpdateProfileRequest,
  UserResponse,
} from './types'

export const currentUserQueryKey = ['auth', 'me'] as const

export async function login(payload: LoginRequest): Promise<AccessTokenResponse> {
  const { data } = await api.post<AccessTokenResponse>('/auth/login', payload)
  return data
}

export async function forgotPassword(
  payload: ForgotPasswordRequest,
): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>('/auth/forgot-password', payload)
  return data
}

export async function resetPassword(payload: ResetPasswordRequest): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>('/auth/reset-password', payload)
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
