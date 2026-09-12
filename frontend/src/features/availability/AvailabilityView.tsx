import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import { fetchMySlots, mySlotsQueryKey, withdrawSlot } from '../../api/availability'
import Icon from '../../components/Icon'
import TableShell from '../../components/TableShell'
import AvailabilityRangeFilter, { type Rango } from './AvailabilityRangeFilter'
import SlotForm from './SlotForm'

const COLUMNAS = ['Desde', 'Hasta', 'Duración', 'Acciones'] as const

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

function calcularVentana(rango: Rango, ancla: string): { desde?: string; hasta?: string } {
  if (rango === 'todos' || ancla === '') {
    return {}
  }
  const inicio = new Date(`${ancla}T00:00:00`)
  const fin = new Date(inicio)
  if (rango === 'dia') {
    fin.setDate(fin.getDate() + 1)
  } else if (rango === 'semana') {
    fin.setDate(fin.getDate() + 7)
  } else {
    fin.setMonth(fin.getMonth() + 1)
  }
  return { desde: inicio.toISOString(), hasta: fin.toISOString() }
}

export default function AvailabilityView() {
  const queryClient = useQueryClient()
  const hoy = new Date().toISOString().slice(0, 10)
  const [rango, setRango] = useState<Rango>('todos')
  const [ancla, setAncla] = useState(hoy)

  const ventana = useMemo(() => calcularVentana(rango, ancla), [rango, ancla])
  const tramos = useQuery({
    queryKey: [...mySlotsQueryKey, ventana],
    queryFn: () => fetchMySlots(ventana.desde, ventana.hasta),
  })

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
        <AvailabilityRangeFilter
          rango={rango}
          ancla={ancla}
          onRangoChange={setRango}
          onAnclaChange={setAncla}
        />
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
