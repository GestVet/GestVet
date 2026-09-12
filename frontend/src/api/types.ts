// Alias sobre el contrato generado desde OpenAPI. Nadie escribe estas formas a
// mano: si el backend cambia un campo, `pnpm generate:api` lo propaga y el
// build del frontend falla en compilacion en vez de fallar en ejecucion.
import type { components } from './schema'

export type HealthResponse = components['schemas']['HealthResponse']

export type UserResponse = components['schemas']['UserResponse']
export type ClientPageResponse = components['schemas']['ClientPageResponse']
export type AccessTokenResponse = components['schemas']['AccessTokenResponse']
export type LoginRequest = components['schemas']['LoginRequest']
export type ForgotPasswordRequest = components['schemas']['ForgotPasswordRequest']
export type ResetPasswordRequest = components['schemas']['ResetPasswordRequest']
export type MessageResponse = components['schemas']['MessageResponse']
export type RegisterClientRequest = components['schemas']['RegisterClientRequest']
export type RegisterStaffRequest = components['schemas']['RegisterStaffRequest']
export type UpdateProfileRequest = components['schemas']['UpdateProfileRequest']
export type VeterinarianResponse = components['schemas']['VeterinarianResponse']
export type VeterinarianListResponse = components['schemas']['VeterinarianListResponse']
export type ActivityResponse = components['schemas']['ActivityResponse']
export type ActivityPageResponse = components['schemas']['ActivityPageResponse']

export type PetResponse = components['schemas']['PetResponse']
export type PetPageResponse = components['schemas']['PetPageResponse']
export type RegisterPetRequest = components['schemas']['RegisterPetRequest']
export type PetSex = components['schemas']['PetSex']
export type UpdatePetOwnerProfileRequest = components['schemas']['UpdatePetOwnerProfileRequest']
export type UpdatePetClinicalProfileRequest =
  components['schemas']['UpdatePetClinicalProfileRequest']

export type SlotResponse = components['schemas']['SlotResponse']
export type SlotListResponse = components['schemas']['SlotListResponse']
export type PublishSlotRequest = components['schemas']['PublishSlotRequest']

export type AppointmentResponse = components['schemas']['AppointmentResponse']
export type AppointmentPageResponse = components['schemas']['AppointmentPageResponse']
export type AppointmentTypeResponse = components['schemas']['AppointmentTypeResponse']
export type AppointmentTypeListResponse = components['schemas']['AppointmentTypeListResponse']
export type BookAppointmentRequest = components['schemas']['BookAppointmentRequest']
export type OpenEmergencyRequest = components['schemas']['OpenEmergencyRequest']

export type ClinicalEntryResponse = components['schemas']['ClinicalEntryResponse']
export type ClinicalEntryPageResponse = components['schemas']['ClinicalEntryPageResponse']
export type AddClinicalEntryRequest = components['schemas']['AddClinicalEntryRequest']
export type EntryKind = components['schemas']['EntryKind']
export type AttachmentResponse = components['schemas']['AttachmentResponse']

export type PaymentResponse = components['schemas']['PaymentResponse']
export type PaymentPageResponse = components['schemas']['PaymentPageResponse']
export type RegisterPaymentRequest = components['schemas']['RegisterPaymentRequest']
export type PaymentMethod = components['schemas']['PaymentMethod']
export type PaymentReportResponse = components['schemas']['PaymentReportResponse']
export type MethodTotalResponse = components['schemas']['MethodTotalResponse']

export type UserRole = UserResponse['role']

export type AppointmentStatus = AppointmentResponse['status']
