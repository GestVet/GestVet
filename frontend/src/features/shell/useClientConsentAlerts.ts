import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'

import { fetchConsents, myPendingConsentsQueryKey } from '../../api/consents'
import { useNotifications } from '../../store/notifications'
import { useCan } from '../../store/session'

// Respaldo: el pedido llega al instante por el canal en tiempo real, que
// invalida esta consulta. El sondeo solo cubre un corte de ese canal.
const POLL_INTERVAL_MS = 60_000

/**
 * Avisa al cliente cuando el veterinario le pide un consentimiento.
 *
 * Compara contra los pendientes que ya vio: el primer vistazo no avisa, para
 * no repetir al entrar lo que la pantalla de consentimientos ya muestra.
 */
export function useClientConsentAlerts(): void {
  const puedeResponder = useCan('consents.respond')
  const push = useNotifications((state) => state.push)
  const anterior = useRef<Set<number> | null>(null)

  const pendientes = useQuery({
    queryKey: myPendingConsentsQueryKey,
    queryFn: () => fetchConsents({ status: 'pending' }),
    enabled: puedeResponder,
    refetchInterval: puedeResponder ? POLL_INTERVAL_MS : false,
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: false,
  })

  useEffect(() => {
    if (!puedeResponder || !pendientes.data) {
      return
    }
    const previa = anterior.current
    if (previa !== null) {
      for (const consent of pendientes.data.items) {
        if (!previa.has(consent.id)) {
          push({
            tone: 'warning',
            message: `Tu veterinario te pidió un consentimiento: ${consent.kind_label} para ${consent.pet_name ?? 'tu mascota'}. Revísalo en Consentimientos.`,
          })
        }
      }
    }
    anterior.current = new Set(pendientes.data.items.map((consent) => consent.id))
  }, [pendientes.data, puedeResponder, push])
}
