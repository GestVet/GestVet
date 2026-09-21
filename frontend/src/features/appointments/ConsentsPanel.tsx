import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { appointmentConsentsQueryKey, fetchConsents } from '../../api/consents'
import ConsentSummary from '../../components/ConsentSummary'
import FormMessage from '../../components/FormMessage'
import { useCan } from '../../store/session'
import type { ConsentDialog } from './consentDialog'
import ConsentDialogHost from './ConsentDialogHost'
import ConsentItemActions from './ConsentItemActions'
import ConsentPanelButtons from './ConsentPanelButtons'
import type { RequestableKind } from './requestConsentSchema'

interface ConsentsPanelProps {
  readonly appointmentId: number
  /** El atajo desde la internación rechazada: abre el pedido con ese tipo elegido. */
  readonly initialRequest?: RequestableKind
}

/**
 * Los consentimientos de la cita: lo pedido, lo respondido y cómo.
 *
 * El veterinario pide, toma la firma en persona o, solo en una emergencia,
 * deja constancia de que atiende sin consentimiento. El cliente ve lo mismo
 * y responde desde su pantalla de consentimientos. El estado se actualiza
 * solo por el canal en tiempo real.
 */
export default function ConsentsPanel({ appointmentId, initialRequest }: ConsentsPanelProps) {
  const puedePedir = useCan('consents.request')
  const [dialogo, setDialogo] = useState<ConsentDialog | null>(
    initialRequest === undefined ? null : { tipo: 'pedir', kind: initialRequest },
  )
  const consentimientos = useQuery({
    queryKey: appointmentConsentsQueryKey(appointmentId),
    queryFn: () => fetchConsents({ appointment_id: appointmentId }),
  })
  const cerrar = () => {
    setDialogo(null)
  }

  if (consentimientos.isError) {
    return <FormMessage tone="error">No se pudieron cargar los consentimientos.</FormMessage>
  }
  if (consentimientos.data === undefined) {
    return <p className="m-0 text-sm text-muted-foreground">Cargando los consentimientos…</p>
  }
  const { items, appointment_is_emergency: esEmergencia } = consentimientos.data

  return (
    <div className="flex flex-col gap-4">
      {items.length === 0 ? (
        <p className="m-0 text-sm text-muted-foreground">
          Esta cita todavía no tiene consentimientos.
        </p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-2 p-0">
          {items.map((consent) => (
            <ConsentSummary key={consent.id} consent={consent}>
              <ConsentItemActions
                consent={consent}
                onSignInPerson={() => {
                  setDialogo({ tipo: 'firmar', consent })
                }}
              />
            </ConsentSummary>
          ))}
        </ul>
      )}

      {puedePedir ? (
        <ConsentPanelButtons isEmergency={esEmergencia === true} onOpen={setDialogo} />
      ) : null}
      <ConsentDialogHost appointmentId={appointmentId} dialog={dialogo} onClose={cerrar} />
    </div>
  )
}
