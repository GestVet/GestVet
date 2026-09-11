import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { fetchMySlots, mySlotsQueryKey, withdrawSlot } from '../../api/availability'
import Icon from '../../components/Icon'
import TableShell from '../../components/TableShell'
import SlotForm from './SlotForm'

const COLUMNAS = ['Desde', 'Hasta', 'Duración', 'Acciones'] as const

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

export default function AvailabilityView() {
  const queryClient = useQueryClient()
  const tramos = useQuery({ queryKey: mySlotsQueryKey, queryFn: fetchMySlots })

  const retirar = useMutation({
    mutationFn: withdrawSlot,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: mySlotsQueryKey })
    },
  })

  const items = tramos.data?.items ?? []

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Mi agenda</h1>
      </div>

      <SlotForm />

      <section className="card">
        <h2>Tramos publicados</h2>
        <TableShell
          columns={COLUMNAS}
          isLoading={tramos.isPending}
          isEmpty={items.length === 0}
          emptyMessage="Todavía no publicaste ningún tramo."
        >
          {items.map((tramo) => (
            <tr key={tramo.id}>
              <td>{FORMATO.format(new Date(tramo.starts_at))}</td>
              <td>{FORMATO.format(new Date(tramo.ends_at))}</td>
              <td>{tramo.duration_minutes} min</td>
              <td>
                <button
                  type="button"
                  className="btn btn-plain"
                  disabled={retirar.isPending}
                  onClick={() => {
                    retirar.mutate(tramo.id)
                  }}
                >
                  <Icon name="cancelar" size={14} />
                  <span>Retirar</span>
                </button>
              </td>
            </tr>
          ))}
        </TableShell>
      </section>
    </div>
  )
}
