// Alias sobre el contrato generado desde OpenAPI. Nadie escribe estas formas a
// mano: si el backend cambia un campo, `pnpm generate:api` lo propaga y el
// build del frontend falla en compilacion en vez de fallar en ejecucion.
import type { components } from './schema'

export type HealthResponse = components['schemas']['HealthResponse']

export type UserResponse = components['schemas']['UserResponse']
export type ClientPageResponse = components['schemas']['ClientPageResponse']
export type AccessTokenResponse = components['schemas']['AccessTokenResponse']
export type LoginRequest = components['schemas']['LoginRequest']
export type RegisterClientRequest = components['schemas']['RegisterClientRequest']
export type RegisterStaffRequest = components['schemas']['RegisterStaffRequest']
export type UpdateProfileRequest = components['schemas']['UpdateProfileRequest']
export type VeterinarianResponse = components['schemas']['VeterinarianResponse']
export type VeterinarianListResponse = components['schemas']['VeterinarianListResponse']

export type PetResponse = components['schemas']['PetResponse']
export type PetPageResponse = components['schemas']['PetPageResponse']
export type RegisterPetRequest = components['schemas']['RegisterPetRequest']

export type SlotResponse = components['schemas']['SlotResponse']
export type SlotListResponse = components['schemas']['SlotListResponse']
export type PublishSlotRequest = components['schemas']['PublishSlotRequest']

export type AppointmentResponse = components['schemas']['AppointmentResponse']
export type AppointmentPageResponse = components['schemas']['AppointmentPageResponse']
export type AppointmentTypeResponse = components['schemas']['AppointmentTypeResponse']
export type AppointmentTypeListResponse = components['schemas']['AppointmentTypeListResponse']
export type BookAppointmentRequest = components['schemas']['BookAppointmentRequest']
export type OpenEmergencyRequest = components['schemas']['OpenEmergencyRequest']

export type UserRole = UserResponse['role']

export type AppointmentStatus = AppointmentResponse['status']
