import { Link } from 'react-router'

import type { ConsentResponse } from '../../api/types'
import { Button } from '../../components/ui/button'
import { useCan } from '../../store/session'

interface ConsentItemActionsProps {
  readonly consent: ConsentResponse
  readonly onSignInPerson: () => void
}

/** Lo que se puede hacer con un pedido pendiente, según quién mira. */
export default function ConsentItemActions({ consent, onSignInPerson }: ConsentItemActionsProps) {
  const puedePedir = useCan('consents.request')
  const puedeResponder = useCan('consents.respond')

  if (consent.status !== 'pending') {
    return null
  }
  if (puedePedir) {
    return (
      <Button type="button" variant="outline" size="sm" className="self-start" onClick={onSignInPerson}>
        Firmar en presencia del responsable
      </Button>
    )
  }
  if (puedeResponder) {
    return (
      <Button asChild variant="outline" size="sm" className="self-start">
        <Link to="/consentimientos">Responder en Consentimientos</Link>
      </Button>
    )
  }
  return null
}
