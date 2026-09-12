import { api } from '../services/api'
import type { ComplaintPageResponse, ComplaintResponse, EvidenceResponse } from './types'

export const complaintsQueryKey = ['complaints'] as const

export async function fetchComplaints(): Promise<ComplaintPageResponse> {
  const { data } = await api.get<ComplaintPageResponse>('/complaints')
  return data
}

export async function fileComplaint(
  appointmentId: number,
  description: string,
): Promise<ComplaintResponse> {
  const { data } = await api.post<ComplaintResponse>('/complaints', {
    appointment_id: appointmentId,
    description,
  })
  return data
}

export async function uploadEvidence(
  complaintId: number,
  file: File,
): Promise<EvidenceResponse> {
  const body = new FormData()
  body.append('file', file)
  const { data } = await api.post<EvidenceResponse>(
    `/complaints/${String(complaintId)}/evidence`,
    body,
    // El navegador arma el separador multipart solo; forzarlo acá pisaría el
    // que ya trae la instancia por defecto para JSON.
    { headers: { 'Content-Type': undefined } },
  )
  return data
}
