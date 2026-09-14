import { useMutation } from '@tanstack/react-query'
import { useRef } from 'react'

import { uploadEvidence } from '../../api/complaints'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'

interface EvidenceUploaderProps {
  readonly complaintId: number
}

/**
 * Adjuntar evidencia a un reclamo ya presentado.
 *
 * El selector se abre con un botón de verdad: una etiqueta con aspecto de
 * botón no se alcanzaba con el teclado.
 */
export default function EvidenceUploader({ complaintId }: EvidenceUploaderProps) {
  const selector = useRef<HTMLInputElement>(null)
  const adjuntar = useMutation({
    mutationFn: (file: File) => uploadEvidence(complaintId, file),
  })

  return (
    <div className="flex flex-col items-start gap-3">
      {adjuntar.isError ? (
        <FormMessage tone="error">
          {errorMessage(adjuntar.error, 'No se pudo adjuntar la evidencia.')}
        </FormMessage>
      ) : null}
      {adjuntar.isSuccess ? (
        <FormMessage tone="ok">Evidencia adjuntada.</FormMessage>
      ) : (
        <>
          <Button
            type="button"
            variant="outline"
            disabled={adjuntar.isPending}
            onClick={() => {
              selector.current?.click()
            }}
          >
            <Icon name="agregar" size={16} />
            <span>{adjuntar.isPending ? 'Subiendo…' : 'Adjuntar evidencia (opcional)'}</span>
          </Button>
          <input
            ref={selector}
            type="file"
            accept="image/jpeg,image/png,image/webp,application/pdf"
            hidden
            onChange={(evento) => {
              const archivo = evento.target.files?.[0]
              evento.target.value = ''
              if (archivo) {
                adjuntar.mutate(archivo)
              }
            }}
          />
        </>
      )}
    </div>
  )
}
