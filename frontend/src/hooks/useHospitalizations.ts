import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  addHospitalizationNote,
  dischargeHospitalization,
  hospitalizationsQueryKey,
} from '../api/hospitalizations'
import { errorMessage } from '../services/api'

interface AddNoteArgs {
  readonly hospitalizationId: number
  readonly note: string
}

/**
 * Mutaciones de internaciones, listas para un componente presentacional.
 *
 * Vive en `hooks/` y no en `features/` porque `HospitalizationList` es un
 * componente compartido (lo usan tanto la vista del cliente, solo lectura,
 * como la del personal) y `components/` no puede importar `api/` directo.
 * Pasando por acá, sí puede.
 */
export function useAddHospitalizationNote(petId: number) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: ({ hospitalizationId, note }: AddNoteArgs) =>
      addHospitalizationNote(hospitalizationId, note),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: hospitalizationsQueryKey(petId) })
    },
  })

  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    isError: mutation.isError,
    errorMessage: mutation.isError
      ? errorMessage(mutation.error, 'No se pudo agregar la nota.')
      : '',
  }
}

export function useDischargeHospitalization(petId: number) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: ({
      hospitalizationId,
      dischargeNotes,
    }: {
      hospitalizationId: number
      dischargeNotes: string
    }) => dischargeHospitalization(hospitalizationId, dischargeNotes),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: hospitalizationsQueryKey(petId) })
    },
  })

  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    isError: mutation.isError,
    errorMessage: mutation.isError
      ? errorMessage(mutation.error, 'No se pudo dar de alta.')
      : '',
  }
}
