import CollapsibleSection from './CollapsibleSection'
import DataTable, { type DataColumn } from './DataTable'
import HospitalizationDetails from './HospitalizationDetails'
import RowExpandButton from './RowExpandButton'
import StatusBadge from './StatusBadge'

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

interface NoteLike {
  readonly id: number
  readonly note: string
  readonly created_at: string
}

/**
 * Forma mínima que este componente necesita. No importa el tipo del contrato
 * generado a propósito: un componente compartido no puede depender de `api`.
 */
interface HospitalizationLike {
  readonly id: number
  readonly reason: string
  readonly status: string
  readonly status_label: string
  readonly discharge_notes: string
  readonly admitted_at: string
  readonly discharged_at: string | null
  readonly notes: readonly NoteLike[]
}

const COLUMNAS: readonly DataColumn<HospitalizationLike>[] = [
  {
    id: 'ingreso',
    header: 'Ingreso',
    cell: (internacion) => FORMATO.format(new Date(internacion.admitted_at)),
  },
  {
    id: 'motivo',
    header: 'Motivo',
    className: 'min-w-48 whitespace-normal',
    cell: (internacion) => internacion.reason,
  },
  {
    id: 'estado',
    header: 'Estado',
    cell: (internacion) => (
      <StatusBadge
        label={internacion.status_label}
        tone={internacion.status === 'open' ? 'pending' : 'completed'}
      />
    ),
  },
  {
    id: 'alta',
    header: 'Alta',
    cell: (internacion) =>
      internacion.discharged_at ? FORMATO.format(new Date(internacion.discharged_at)) : '—',
  },
  {
    id: 'notas',
    header: 'Notas',
    cell: (internacion, fila) => (
      <RowExpandButton
        isExpanded={fila.isExpanded}
        onToggle={fila.toggleExpanded}
        collapsedLabel={`Ver notas (${String(internacion.notes.length)})`}
        expandedLabel="Ocultar notas"
      />
    ),
  },
]

interface HospitalizationListProps {
  readonly items: readonly HospitalizationLike[]
  readonly isLoading: boolean
  readonly petId: number
  readonly canManage: boolean
}

/**
 * Lista de internaciones de una mascota.
 *
 * Puramente presentacional: no pide los datos, los recibe. Así la usan tanto
 * la vista del cliente (solo lectura) como la del personal (con notas y alta),
 * sin que ninguna de las dos características tenga que importar a la otra.
 */
export default function HospitalizationList({
  items,
  isLoading,
  petId,
  canManage,
}: HospitalizationListProps) {
  return (
    // Cerrada al empezar: casi ninguna mascota tiene internaciones.
    <CollapsibleSection title="Internaciones" defaultOpen={false}>
      <DataTable
        columns={COLUMNAS}
        data={items}
        isLoading={isLoading}
        emptyMessage="Esta mascota nunca fue internada."
        getRowId={(internacion) => String(internacion.id)}
        pageSize={10}
        renderExpanded={(internacion) => (
          <HospitalizationDetails internacion={internacion} petId={petId} canManage={canManage} />
        )}
      />
    </CollapsibleSection>
  )
}
