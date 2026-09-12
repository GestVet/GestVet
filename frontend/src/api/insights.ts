import { api } from '../services/api'
import type {
  CareReminderListResponse,
  NoShowRiskListResponse,
  PaymentAnomalyListResponse,
  VeterinarianAlertListResponse,
} from './types'

export const careRemindersQueryKey = ['insights', 'care-reminders'] as const
export const noShowRisksQueryKey = ['insights', 'no-show-risks'] as const
export const paymentAnomaliesQueryKey = ['insights', 'payment-anomalies'] as const
export const veterinarianAlertsQueryKey = ['insights', 'veterinarian-alerts'] as const

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
