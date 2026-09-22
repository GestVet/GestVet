import { useQuery } from '@tanstack/react-query'

import { fetchConsents, myConsentsQueryKey } from '../../api/consents'
import ConsentSummary from '../../components/ConsentSummary'
import EmptyState from '../../components/EmptyState'
import PageHeader from '../../components/PageHeader'
import SectionCard from '../../components/SectionCard'
import { useSession } from '../../store/session'
import PendingConsentCard from './PendingConsentCard'

/**
 * Los consentimientos que el veterinario pidió sobre las mascotas del cliente.
 *
 * Primero lo que espera respuesta, con el texto completo para leerlo antes de
 * decidir; después el historial. Un pedido nuevo llega por el canal en tiempo
 * real y aparece sin recargar.
 */
export default function ConsentsView() {
  const usuario = useSession((state) => state.user)
  const firmante = usuario === null ? '' : `${usuario.first_name} ${usuario.last_name}`.trim()
  const consentimientos = useQuery({
    queryKey: myConsentsQueryKey,
    queryFn: () => fetchConsents(),
  })
  const items = consentimientos.data?.items ?? []
  const pendientes = items.filter((consent) => consent.status === 'pending')
  const historial = items.filter((consent) => consent.status !== 'pending')

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Consentimientos"
        description="Lo que tu veterinario te pide autorizar sobre la atención de tus mascotas."
      />
      {consentimientos.isPending ? <EmptyState title="Cargando consentimientos…" /> : null}
      {consentimientos.isError ? (
        <EmptyState title="No se pudieron cargar los consentimientos." />
      ) : null}

      {consentimientos.isSuccess && pendientes.length === 0 ? (
        <EmptyState title="No tienes consentimientos por responder." />
      ) : null}
      {pendientes.length > 0 ? (
        <ul className="m-0 flex list-none flex-col gap-4 p-0" aria-label="Por responder">
          {pendientes.map((consent) => (
            <li key={consent.id}>
              <PendingConsentCard consent={consent} defaultSignerName={firmante} />
            </li>
          ))}
        </ul>
      ) : null}

      {historial.length > 0 ? (
        <SectionCard title="Historial">
          <ul className="m-0 flex list-none flex-col gap-2 p-0">
            {historial.map((consent) => (
              <ConsentSummary key={consent.id} consent={consent} />
            ))}
          </ul>
        </SectionCard>
      ) : null}
    </div>
  )
}
