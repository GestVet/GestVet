import type { ComplaintResponse } from '../../api/types'
import ComplaintEvidence from './ComplaintEvidence'

const FECHA_Y_HORA = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

interface ComplaintCardProps {
  readonly reclamo: ComplaintResponse
}

function descripcionDeCita(reclamo: ComplaintResponse): string {
  if (reclamo.appointment_at === null) {
    return 'Cita no disponible'
  }
  const cuando = FECHA_Y_HORA.format(new Date(reclamo.appointment_at))
  return reclamo.appointment_type === '' ? cuando : `${reclamo.appointment_type}, ${cuando}`
}

/** Un reclamo: quién lo presenta, sobre quién, de qué cita, qué pasó y su evidencia. */
export default function ComplaintCard({ reclamo }: ComplaintCardProps) {
  const tituloId = `reclamo-${String(reclamo.id)}`
  const datos: readonly [string, string][] = [
    ['Veterinario', reclamo.veterinarian_name || '—'],
    ['Mascota', reclamo.pet_name || '—'],
    ['Cita', descripcionDeCita(reclamo)],
  ]

  return (
    <article
      aria-labelledby={tituloId}
      className="flex flex-col gap-4 rounded-xl bg-card p-4 shadow-sm ring-1 ring-foreground/10 sm:p-5"
    >
      <header className="flex flex-col gap-0.5">
        <h2 id={tituloId} className="m-0 font-heading text-base leading-snug font-semibold">
          Reclamo de {reclamo.client_name || 'un cliente'}
        </h2>
        <p className="m-0 text-sm text-muted-foreground">
          Presentado el {FECHA_Y_HORA.format(new Date(reclamo.created_at))}
        </p>
      </header>

      <dl className="m-0 grid gap-3 text-sm sm:grid-cols-3">
        {datos.map(([etiqueta, valor]) => (
          <div key={etiqueta} className="flex flex-col gap-0.5">
            <dt className="text-muted-foreground">{etiqueta}</dt>
            <dd className="m-0 font-medium">{valor}</dd>
          </div>
        ))}
      </dl>

      <div className="flex flex-col gap-1.5">
        <p className="m-0 text-sm font-medium">Qué pasó</p>
        <blockquote className="m-0 rounded-md border-l-4 border-primary/40 bg-muted/40 px-3 py-2 text-sm leading-relaxed whitespace-pre-line">
          {reclamo.description}
        </blockquote>
      </div>

      <ComplaintEvidence archivos={reclamo.evidence} />
    </article>
  )
}
