import { api } from '../services/api'

// eslint-disable-next-line sonarjs/todo-tag -- el backend publica este contrato en paralelo; el TODO es el recordatorio de reemplazar los tipos locales por los generados.
// TODO: reemplazar estos tipos por los generados en `schema.d.ts` cuando el
// backend publique el contrato de /auth/me/layout y se corra `pnpm generate:api`.
// Hasta entonces son la forma local del mismo contrato.
export interface DashboardBlockPreference {
  readonly id: string
  readonly visible: boolean
}

export interface LayoutPreferencesResponse {
  readonly sidebar_order: readonly string[]
  readonly dashboard_blocks: readonly DashboardBlockPreference[]
  readonly updated_at: string | null
}

export interface LayoutPreferencesRequest {
  readonly sidebar_order: readonly string[]
  readonly dashboard_blocks: readonly DashboardBlockPreference[]
}

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
