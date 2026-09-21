import { useMutation, useQueryClient } from '@tanstack/react-query'

import { acceptConsentInPerson, consentsQueryKey } from '../../api/consents'
import type { ConsentResponse } from '../../api/types'
import ConsentSignForm from '../../components/ConsentSignForm'
import ConsentText from '../../components/ConsentText'
import { signedContent } from '../../components/consentSnapshot'
import FormDialog from '../../components/FormDialog'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'

interface InPersonSignDialogProps {
  readonly consent: ConsentResponse
  readonly onClose: () => void
}

/**
 * El responsable firma en la pantalla del veterinario.
 *
 * El veterinario le pasa el dispositivo: el responsable lee el texto, marca la
 * casilla y escribe su nombre. El veterinario queda como testigo.
 */
export default function InPersonSignDialog({ consent, onClose }: InPersonSignDialogProps) {
  const queryClient = useQueryClient()
  const firmar = useMutation({
    mutationFn: (signerName: string) =>
      acceptConsentInPerson(consent.id, { signer_name: signerName, accepted: true }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: consentsQueryKey })
      onClose()
    },
  })

  return (
    <FormDialog
      open
      onOpenChange={(abierto) => {
        if (!abierto) {
          onClose()
        }
      }}
      title="Firma en presencia del responsable"
      description="Entrega el dispositivo al responsable para que lea el texto y firme. Tú quedas como testigo."
      size="lg"
    >
      <div className="flex flex-col gap-4">
        <ConsentText
          id={`consentimiento-${String(consent.id)}-texto`}
          template={signedContent(consent)}
          isError={false}
        />
        <ConsentSignForm
          id={`consentimiento-${String(consent.id)}-presencial`}
          defaultSignerName=""
          checkboxLabel="Leí el texto y lo acepto"
          submitLabel="Firmar"
          isPending={firmar.isPending}
          error={
            firmar.isError
              ? errorMessage(firmar.error, 'No se pudo registrar la firma.')
              : undefined
          }
          onSign={(nombre) => {
            firmar.mutate(nombre)
          }}
        >
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
        </ConsentSignForm>
      </div>
    </FormDialog>
  )
}
