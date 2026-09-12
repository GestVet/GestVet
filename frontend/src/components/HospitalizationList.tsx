import HospitalizationRow from './HospitalizationRow'
import TableShell from './TableShell'

const COLUMNAS = ['Ingreso', 'Motivo', 'Estado', 'Alta', 'Notas'] as const

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
    <div className="stack">
      <h3>Internaciones</h3>
      <TableShell
        columns={COLUMNAS}
        isLoading={isLoading}
        isEmpty={items.length === 0}
        emptyMessage="Esta mascota nunca fue internada."
      >
        {items.map((internacion) => (
          <HospitalizationRow
            key={internacion.id}
            internacion={internacion}
            petId={petId}
            canManage={canManage}
          />
        ))}
      </TableShell>
    </div>
  )
}
