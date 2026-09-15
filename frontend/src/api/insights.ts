import { api } from '../services/api'
import type {
  CareReminderListResponse,
  NoShowRiskListResponse,
  PaymentAnomalyListResponse,
  PetOverviewListResponse,
  ServiceConsumptionListResponse,
  VeterinarianAlertListResponse,
} from './types'

export const careRemindersQueryKey = ['insights', 'care-reminders'] as const
export const noShowRisksQueryKey = ['insights', 'no-show-risks'] as const
export const paymentAnomaliesQueryKey = ['insights', 'payment-anomalies'] as const
export const veterinarianAlertsQueryKey = ['insights', 'veterinarian-alerts'] as const
export const petsOverviewQueryKey = ['insights', 'pets-overview'] as const

export interface ServiceConsumptionFilter {
  readonly starts_after?: string
  readonly ends_before?: string
  readonly status?: string
}

export function serviceConsumptionQueryKey(filter: ServiceConsumptionFilter) {
  return ['insights', 'service-consumption', filter] as const
}

export async function fetchCareReminders(): Promise<CareReminderListResponse> {
  const { data } = await api.get<CareReminderListResponse>('/insights/care-reminders')
  return data
}

export async function fetchNoShowRisks(): Promise<NoShowRiskListResponse> {
  const { data } = await api.get<NoShowRiskListResponse>('/insights/no-show-risks')
  return data
}

export async function fetchPaymentAnomalies(): Promise<PaymentAnomalyListResponse> {
  const { data } = await api.get<PaymentAnomalyListResponse>('/insights/payment-anomalies')
  return data
}

export async function fetchVeterinarianAlerts(): Promise<VeterinarianAlertListResponse> {
  const { data } = await api.get<VeterinarianAlertListResponse>('/insights/veterinarian-alerts')
  return data
}

export async function fetchPetsOverview(): Promise<PetOverviewListResponse> {
  const { data } = await api.get<PetOverviewListResponse>('/insights/pets-overview')
  return data
}

export async function fetchServiceConsumption(
  filter: ServiceConsumptionFilter = {},
): Promise<ServiceConsumptionListResponse> {
  const { data } = await api.get<ServiceConsumptionListResponse>('/insights/service-consumption', {
    params: filter,
  })
  return data
}

export async function downloadServiceConsumptionPdf(
  filter: ServiceConsumptionFilter = {},
): Promise<Blob> {
  const { data } = await api.get<Blob>('/insights/service-consumption.pdf', {
    params: filter,
    responseType: 'blob',
  })
  return data
}
