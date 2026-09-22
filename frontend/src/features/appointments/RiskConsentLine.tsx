import { useQuery } from '@tanstack/react-query'

import { consentQueryKey, fetchConsent } from '../../api/consents'
import Icon from '../../components/Icon'

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

interface RiskConsentLineProps {
  readonly consentId: number
}

/** Quién aceptó el riesgo de la emergencia, cuándo y por qué vía. */
export default function RiskConsentLine({ consentId }: RiskConsentLineProps) {
  const consentimiento = useQuery({
    queryKey: consentQueryKey(consentId),
    queryFn: () => fetchConsent(consentId),
    // Un consentimiento firmado no cambia nunca.
    staleTime: Infinity,
  })

  if (consentimiento.isError) {
    return (
      <p className="m-0 text-sm text-muted-foreground">
        No se pudo cargar la aceptación del riesgo.
      </p>
    )
  }
  if (consentimiento.data === undefined) {
    return <p className="m-0 text-sm text-muted-foreground">Cargando la aceptación del riesgo…</p>
  }

  const {
    signer_name: firmante,
    decided_at: firmado,
    created_at: creado,
    channel_label: canal,
  } = consentimiento.data

  return (
    <p className="m-0 flex items-start gap-2 text-sm text-foreground">
      <Icon name="permisos" size={16} className="mt-0.5 shrink-0 text-success" />
      <span>
        Riesgo aceptado por <strong className="font-semibold">{firmante ?? '—'}</strong> ·{' '}
        {FORMATO.format(new Date(firmado ?? creado))} · {canal ?? '—'}
      </span>
    </p>
  )
}
