import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { consentsQueryKey, declineConsent } from '../../api/consents'
import type { ConsentResponse } from '../../api/types'
import DialogFormActions from '../../components/DialogFormActions'
import FormDialog from '../../components/FormDialog'
import FormMessage from '../../components/FormMessage'
import { Button } from '../../components/ui/button'
import { Label } from '../../components/ui/label'
import { Textarea } from '../../components/ui/textarea'
import { errorMessage } from '../../services/api'

// El mismo tope que el servidor.
const MAX_MOTIVO = 500

interface DeclineConsentDialogProps {
  readonly consent: ConsentResponse
}

/**
 * Rechazar un pedido, con un motivo opcional.
 *
 * Rechazar no firma nada, así que no pide nombre. Sí recuerda llamar a la
 * clínica: el veterinario necesita saber cómo seguir con la atención.
 */
export default function DeclineConsentDialog({ consent }: DeclineConsentDialogProps) {
  const queryClient = useQueryClient()
  const [abierto, setAbierto] = useState(false)
  const [motivo, setMotivo] = useState('')
  const rechazar = useMutation({
    mutationFn: () => declineConsent(consent.id, { reason: motivo.trim() || null }),
    onSuccess: () => {
      setAbierto(false)
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: consentsQueryKey })
    },
  })
  const idMotivo = `rechazo-${String(consent.id)}-motivo`

  return (
    <>
      <Button
        type="button"
        variant="outline"
        onClick={() => {
          setAbierto(true)
        }}
      >
        Rechazar
      </Button>
      <FormDialog
        open={abierto}
        onOpenChange={setAbierto}
        title="¿Rechazar este consentimiento?"
        description={`${consent.kind_label} para ${consent.pet_name ?? 'tu mascota'}. Tu veterinario verá el rechazo al instante.`}
      >
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor={idMotivo}>Motivo (opcional)</Label>
            <Textarea
              id={idMotivo}
              rows={3}
              maxLength={MAX_MOTIVO}
              value={motivo}
              onChange={(evento) => {
                setMotivo(evento.target.value)
              }}
            />
          </div>
          <p className="m-0 text-sm text-muted-foreground">
            Llama a la clínica para conversar con tu veterinario sobre cómo seguir con la atención.
          </p>
          {rechazar.isError ? (
            <FormMessage tone="error">
              {errorMessage(rechazar.error, 'No se pudo registrar el rechazo.')}
            </FormMessage>
          ) : null}
          <DialogFormActions>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setAbierto(false)
              }}
            >
              Volver
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={rechazar.isPending}
              onClick={() => {
                rechazar.mutate()
              }}
            >
              {rechazar.isPending ? 'Rechazando…' : 'Rechazar'}
            </Button>
          </DialogFormActions>
        </div>
      </FormDialog>
    </>
  )
}
