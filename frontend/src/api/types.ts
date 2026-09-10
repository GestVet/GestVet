// Alias sobre el contrato generado desde OpenAPI. Nadie escribe estas formas a
// mano: si el backend cambia un campo, `pnpm generate:api` lo propaga y el
// build del frontend falla en compilación en vez de fallar en ejecución.
import type { components } from './schema'

export type HealthResponse = components['schemas']['HealthResponse']
export type UserResponse = components['schemas']['UserResponse']
export type ClientPageResponse = components['schemas']['ClientPageResponse']
export type AccessTokenResponse = components['schemas']['AccessTokenResponse']
export type LoginRequest = components['schemas']['LoginRequest']
export type RegisterClientRequest = components['schemas']['RegisterClientRequest']
