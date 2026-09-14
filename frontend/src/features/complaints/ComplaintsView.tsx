import { useQuery } from '@tanstack/react-query'

import { complaintsQueryKey, fetchComplaints } from '../../api/complaints'
import EmptyState from '../../components/EmptyState'
import PageHeader from '../../components/PageHeader'
import TablePagination from '../../components/TablePagination'
import { usePagination } from '../../hooks/usePagination'
import ComplaintCard from './ComplaintCard'

const RECLAMOS_POR_PAGINA = 10

/**
 * Los reclamos de los clientes, uno por tarjeta.
 *
 * Antes era una tabla con números de cliente, veterinario y cita que nadie
 * podía interpretar sin ir a buscarlos. Cada tarjeta dice quién reclama, sobre
 * quién, de qué mascota y en qué cita, con lo que pasó y la evidencia a la vista.
 */
export default function ComplaintsView() {
  const reclamos = useQuery({ queryKey: complaintsQueryKey, queryFn: fetchComplaints })
  const items = reclamos.data?.items ?? []
  const pagina = usePagination(items, RECLAMOS_POR_PAGINA)
  const vacio = !reclamos.isPending && items.length === 0

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Reclamos"
        description="Lo que presentan los clientes sobre la atención de una cita, el más reciente primero."
      />
      {reclamos.isPending ? <EmptyState title="Cargando reclamos…" /> : null}
      {vacio ? <EmptyState title="Todavía no hay reclamos registrados." /> : null}
      <ul className="m-0 flex list-none flex-col gap-4 p-0">
        {pagina.visibles.map((reclamo) => (
          <li key={reclamo.id}>
            <ComplaintCard reclamo={reclamo} />
          </li>
        ))}
      </ul>
      {pagina.total > 1 ? (
        <TablePagination actual={pagina.actual} total={pagina.total} onChange={pagina.irA} />
      ) : null}
    </div>
  )
}
