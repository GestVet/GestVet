import { useMutation } from '@tanstack/react-query'

import { downloadClinicalHistoryReport } from '../api/medicalRecords'
import { errorMessage } from '../services/api'
import { guardarArchivo } from '../services/descargas'

/**
 * Descarga el PDF y dispara el guardado, listo para un componente
 * presentacional. Vive en `hooks/` por la misma razón que
 * `useAttachments`: `components/` no puede importar `api/` directo.
 */
export function useClinicalHistoryReport(petId: number) {
  const mutation = useMutation({
    mutationFn: async () => {
      const blob = await downloadClinicalHistoryReport(petId)
      guardarArchivo(blob, `historia-clinica-${String(petId)}.pdf`)
    },
  })

  return {
    mutate: mutation.mutate,
    isPending: mutation.isPending,
    isError: mutation.isError,
    errorMessage: mutation.isError
      ? errorMessage(mutation.error, 'No se pudo generar el PDF.')
      : '',
  }
}
