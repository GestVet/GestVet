import { api } from '../services/api'
import type { HealthResponse } from './types'

export const healthQueryKey = ['health'] as const

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/health')
  return data
}
