import { api } from '../services/api'
import type { AttachmentResponse } from './types'

export async function uploadAttachment(
  clinicalEntryId: number,
  file: File,
): Promise<AttachmentResponse> {
  const body = new FormData()
  body.append('file', file)
  const { data } = await api.post<AttachmentResponse>(
    `/medical-records/${String(clinicalEntryId)}/attachments`,
    body,
    // El navegador arma el separador multipart solo; forzarlo acá pisaría el
    // que ya trae la instancia por defecto para JSON.
    { headers: { 'Content-Type': undefined } },
  )
  return data
}

export async function deleteAttachment(attachmentId: number): Promise<void> {
  await api.delete(`/medical-records/attachments/${String(attachmentId)}`)
}

/** El archivo de un adjunto. No tiene dirección pública: se pide con la sesión. */
export async function fetchAttachmentFile(attachmentId: number): Promise<Blob> {
  const { data } = await api.get<Blob>(
    `/medical-records/attachments/${String(attachmentId)}/file`,
    { responseType: 'blob' },
  )
  return data
}
