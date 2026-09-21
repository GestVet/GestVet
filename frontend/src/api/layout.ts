import { api } from '../services/api'
import type { components } from './schema'

// El contrato de /auth/me/layout ya vive en `schema.d.ts`, que se regenera con
// `pnpm generate:api`; estos alias solo le ponen nombre a esos tipos.
export type DashboardBlockPreference =
  components['schemas']['DashboardBlockPreferenceSchema']
export type LayoutPreferencesResponse = components['schemas']['LayoutPreferencesResponse']
export type LayoutPreferencesRequest = components['schemas']['LayoutPreferencesRequest']

const LAYOUT_PATH = '/auth/me/layout'

export async function fetchLayout(): Promise<LayoutPreferencesResponse> {
  const { data } = await api.get<LayoutPreferencesResponse>(LAYOUT_PATH)
  return data
}

export async function saveLayout(
  payload: LayoutPreferencesRequest,
): Promise<LayoutPreferencesResponse> {
  const { data } = await api.put<LayoutPreferencesResponse>(LAYOUT_PATH, payload)
  return data
}

export async function deleteLayout(): Promise<void> {
  await api.delete(LAYOUT_PATH)
}
