import type { ClinicalSummaryResponse } from '../../api/types'
import ClinicalSummaryList from './ClinicalSummaryList'

const HORA = new Intl.DateTimeFormat('es-PE', { timeStyle: 'short' })

interface ClinicalSummaryResultProps {
  readonly resultado: ClinicalSummaryResponse
}

/** Lo que devolvió el asistente, con la advertencia de revisarlo antes de decidir. */
export default function ClinicalSummaryResult({ resultado }: ClinicalSummaryResultProps) {
  return (
    <div className="flex flex-col gap-4">
      <p className="m-0 text-sm leading-relaxed">{resultado.summary}</p>
      {resultado.alerts.length > 0 ? (
        <ClinicalSummaryList titulo="Alertas" icono="alerta" items={resultado.alerts} />
      ) : null}
      {resultado.follow_ups.length > 0 ? (
        <ClinicalSummaryList titulo="Pendientes" icono="agenda" items={resultado.follow_ups} />
      ) : null}
      <p className="m-0 text-xs text-muted-foreground">
        Generado con IA a las {HORA.format(new Date(resultado.generated_at))} a partir de la
        historia registrada. Puede equivocarse: revísalo antes de decidir.
      </p>
    </div>
  )
}
