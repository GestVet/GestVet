import { useMutation } from '@tanstack/react-query'

import { downloadVaccinationCardPdf } from '../api/medicalRecords'
import { errorMessage } from '../services/api'
import { guardarArchivo } from '../services/descargas'

/** Baja el carnet de vacunas en PDF, listo para un componente compartido. */
export function useVaccinationCardPdf(petId: number) {
  const mutation = useMutation({
    mutationFn: async () => {
      const blob = await downloadVaccinationCardPdf(petId)
      guardarArchivo(blob, `carnet-de-vacunas-${String(petId)}.pdf`)
    },
  })

  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    isError: mutation.isError,
    errorMessage: mutation.isError
      ? errorMessage(mutation.error, 'No se pudo generar el carnet.')
      : '',
  }
}
