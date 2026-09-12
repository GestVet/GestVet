import { useMutation } from '@tanstack/react-query'

import { uploadEvidence } from '../../api/complaints'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { errorMessage } from '../../services/api'

interface EvidenceUploaderProps {
  readonly complaintId: number
}

/** Adjuntar evidencia a un reclamo ya presentado. */
export default function EvidenceUploader({ complaintId }: EvidenceUploaderProps) {
  const adjuntar = useMutation({
    mutationFn: (file: File) => uploadEvidence(complaintId, file),
  })

  return (
    <div className="stack">
      {adjuntar.isError ? (
        <FormMessage tone="error">
          {errorMessage(adjuntar.error, 'No se pudo adjuntar la evidencia.')}
        </FormMessage>
      ) : null}
      {adjuntar.isSuccess ? (
        <FormMessage tone="ok">Evidencia adjuntada.</FormMessage>
      ) : (
        <label className="btn btn-plain" style={{ width: 'fit-content' }}>
          <Icon name="agregar" size={16} />
          <span>{adjuntar.isPending ? 'Subiendo…' : 'Adjuntar evidencia (opcional)'}</span>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp,application/pdf"
            hidden
            disabled={adjuntar.isPending}
            onChange={(evento) => {
              const archivo = evento.target.files?.[0]
              evento.target.value = ''
              if (archivo) {
                adjuntar.mutate(archivo)
              }
            }}
          />
        </label>
      )}
    </div>
  )
}
