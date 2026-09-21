import type { ReactNode } from 'react'

import { type ConsentLike, consentDecisionLine, consentTone } from './consentSnapshot'
import StatusBadge from './StatusBadge'

interface ConsentSummaryProps {
  readonly consent: ConsentLike
  /** Lo que va debajo de la línea de estado: acciones o el texto completo. */
  readonly children?: ReactNode
}

/** Un consentimiento en una lista: tipo, estado, quién respondió y los motivos. */
export default function ConsentSummary({ consent, children }: ConsentSummaryProps) {
  return (
    <li className="flex flex-col gap-2 rounded-lg border border-border bg-card px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="m-0 text-sm font-semibold text-foreground">
          {consent.kind_label}
          {consent.pet_name === null ? null : (
            <span className="font-normal text-muted-foreground"> · {consent.pet_name}</span>
          )}
        </p>
        <StatusBadge label={consent.status_label} tone={consentTone(consent.status)} />
      </div>
      <p className="m-0 text-xs text-muted-foreground">{consentDecisionLine(consent)}</p>
      {consent.details?.procedure ? (
        <p className="m-0 text-sm text-foreground">Procedimiento: {consent.details.procedure}</p>
      ) : null}
      {consent.decision_reason === null ? null : (
        <p className="m-0 text-sm text-foreground">
          {consent.status === 'waived_emergency' ? 'Justificación' : 'Motivo'}:{' '}
          {consent.decision_reason}
        </p>
      )}
      {children}
    </li>
  )
}
