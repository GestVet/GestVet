import { api } from '../services/api'
import type {
  PaymentMethod,
  PaymentPageResponse,
  PaymentReportResponse,
  PaymentResponse,
  QrChargeResponse,
  RegisterPaymentRequest,
} from './types'

export interface PaymentsFilter {
  readonly appointment_id?: number
  readonly method?: PaymentMethod
  readonly starts_after?: string
  readonly ends_before?: string
}

export function paymentsQueryKey(filter: PaymentsFilter) {
  return ['payments', filter] as const
}

export function paymentReportQueryKey(filter: PaymentsFilter) {
  return ['payments', 'report', filter] as const
}

export async function fetchPayments(filter: PaymentsFilter = {}): Promise<PaymentPageResponse> {
  const { data } = await api.get<PaymentPageResponse>('/payments', { params: filter })
  return data
}

export async function registerPayment(
  payload: RegisterPaymentRequest,
): Promise<PaymentResponse> {
  const { data } = await api.post<PaymentResponse>('/payments', payload)
  return data
}

export async function voidPayment(paymentId: number, reason: string): Promise<PaymentResponse> {
  const { data } = await api.post<PaymentResponse>(`/payments/${String(paymentId)}/void`, {
    reason,
  })
  return data
}

export async function fetchPaymentReport(
  filter: PaymentsFilter = {},
): Promise<PaymentReportResponse> {
  const { data } = await api.get<PaymentReportResponse>('/payments/report', { params: filter })
  return data
}

export function qrChargeQueryKey(chargeId: number) {
  return ['payments', 'qr-charge', chargeId] as const
}

export async function createQrCharge(appointmentId: number): Promise<QrChargeResponse> {
  const { data } = await api.post<QrChargeResponse>('/payments/qr-charges', {
    appointment_id: appointmentId,
  })
  return data
}

export async function fetchQrCharge(chargeId: number): Promise<QrChargeResponse> {
  const { data } = await api.get<QrChargeResponse>(`/payments/qr-charges/${String(chargeId)}`)
  return data
}

export async function confirmQrCharge(chargeId: number): Promise<QrChargeResponse> {
  const { data } = await api.post<QrChargeResponse>(
    `/payments/qr-charges/${String(chargeId)}/confirm`,
  )
  return data
}
