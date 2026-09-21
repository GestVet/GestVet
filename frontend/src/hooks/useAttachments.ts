import { useMutation, useQueryClient } from '@tanstack/react-query'

import { deleteAttachment, fetchAttachmentFile, uploadAttachment } from '../api/attachments'
import { clinicalEntriesQueryKey } from '../api/medicalRecords'
import { errorMessage } from '../services/api'
import { useFileOpener } from './useFileOpener'

interface UploadArgs {
  readonly clinicalEntryId: number
  readonly file: File
}

/**
 * Mutaciones de adjuntos, listas para un componente presentacional.
 *
 * Vive en `hooks/` y no en `features/` porque `AttachmentsPanel` es un
 * componente compartido (lo usan tanto la vista del cliente como la del
 * personal) y `components/` no puede importar `api/` directo. Pasando por
 * acá, sí puede: `components` → `hooks` → `api` respeta el límite de
 * dependencias entre capas.
 */
export function useAttachmentUpload(petId: number) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: ({ clinicalEntryId, file }: UploadArgs) =>
      uploadAttachment(clinicalEntryId, file),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: clinicalEntriesQueryKey(petId) })
    },
  })

  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    isError: mutation.isError,
    errorMessage: mutation.isError
      ? errorMessage(mutation.error, 'No se pudo subir el archivo.')
      : '',
  }
}

export function useAttachmentDelete(petId: number) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (attachmentId: number) => deleteAttachment(attachmentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: clinicalEntriesQueryKey(petId) })
    },
  })

  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    isError: mutation.isError,
    errorMessage: mutation.isError
      ? errorMessage(mutation.error, 'No se pudo quitar el adjunto.')
      : '',
  }
}

export function useAttachmentOpener() {
  return useFileOpener(fetchAttachmentFile)
}
