import { useMutation, useQueryClient } from '@tanstack/react-query'

import { updatePetClinicalProfile, updatePetOwnerProfile } from '../api/pets'
import type { UpdatePetClinicalProfileRequest, UpdatePetOwnerProfileRequest } from '../api/types'
import { errorMessage } from '../services/api'

/**
 * Actualiza el perfil de una mascota, listo para un componente
 * presentacional. Vive en `hooks/` por la misma razón que `useAttachments`:
 * `components/` no puede importar `api/` directo.
 *
 * Invalida el espacio completo de claves `pets`, sin distinguir `mine` de
 * `owner/<id>`: el panel se usa tanto desde la vista del cliente como desde
 * la del personal, y no siempre sabe bajo cuál de las dos listas está.
 */
export function usePetOwnerProfileUpdate(petId: number) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (payload: UpdatePetOwnerProfileRequest) => updatePetOwnerProfile(petId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['pets'] })
    },
  })

  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    isError: mutation.isError,
    errorMessage: mutation.isError
      ? errorMessage(mutation.error, 'No se pudo guardar el perfil.')
      : '',
  }
}

export function usePetClinicalProfileUpdate(petId: number) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (payload: UpdatePetClinicalProfileRequest) =>
      updatePetClinicalProfile(petId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['pets'] })
    },
  })

  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    isError: mutation.isError,
    errorMessage: mutation.isError
      ? errorMessage(mutation.error, 'No se pudieron guardar los datos clínicos.')
      : '',
  }
}
