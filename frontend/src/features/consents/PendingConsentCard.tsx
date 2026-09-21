import { useMutation, useQueryClient } from '@tanstack/react-query'

import { acceptConsent, consentsQueryKey } from '../../api/consents'
import type { ConsentResponse } from '../../api/types'
import ConsentSignForm from '../../components/ConsentSignForm'
import ConsentText from '../../components/ConsentText'
import { formatConsentDate, signedContent } from '../../components/consentSnapshot'
import SectionCard from '../../components/SectionCard'
import { errorMessage } from '../../services/api'
import DeclineConsentDialog from './DeclineConsentDialog'

interface PendingConsentCardProps {
  readonly consent: ConsentResponse
  readonly defaultSignerName: string
}

/** Un pedido por responder: sobre qué mascota, quién lo pide, el texto y las dos respuestas. */
export default function PendingConsentCard({ consent, defaultSignerName }: PendingConsentCardProps) {
  const queryClient = useQueryClient()
  const aceptar = useMutation({
    mutationFn: (signerName: string) =>
      acceptConsent(consent.id, { signer_name: signerName, accepted: true }),
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: consentsQueryKey })
    },
  })
  const id = `consentimiento-${String(consent.id)}`

  return (
    <SectionCard
      title={`${consent.kind_label} · ${consent.pet_name ?? 'tu mascota'}`}
      description={
        <>
          Pedido por {consent.requested_by_name ?? 'tu veterinario'} el{' '}
          {formatConsentDate(consent.created_at)}
          {consent.expires_at === null ? null : (
            <> · responde antes del {formatConsentDate(consent.expires_at)}</>
          )}
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <ConsentText id={`${id}-texto`} template={signedContent(consent)} isError={false} />
        <ConsentSignForm
          id={id}
          defaultSignerName={defaultSignerName}
          checkboxLabel="Leí el texto y lo acepto"
          submitLabel="Aceptar"
          isPending={aceptar.isPending}
          error={
            aceptar.isError
              ? errorMessage(aceptar.error, 'No se pudo registrar tu respuesta.')
              : undefined
          }
          onSign={(nombre) => {
            aceptar.mutate(nombre)
          }}
        >
          <DeclineConsentDialog consent={consent} />
        </ConsentSignForm>
      </div>
    </SectionCard>
  )
}
