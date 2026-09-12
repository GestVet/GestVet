import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'

import { fetchMySlots, mySlotsQueryKey } from '../../api/availability'
import DataTable, { type DataColumn } from '../../components/DataTable'
import PageHeader from '../../components/PageHeader'
import SectionCard from '../../components/SectionCard'
import AvailabilityRangeFilter, { type Rango } from './AvailabilityRangeFilter'
import SlotForm from './SlotForm'
import WithdrawSlotButton from './WithdrawSlotButton'

type Tramo = Awaited<ReturnType<typeof fetchMySlots>>['items'][number]

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

const COLUMNAS: readonly DataColumn<Tramo>[] = [
  { id: 'desde', header: 'Desde', cell: (tramo) => FORMATO.format(new Date(tramo.starts_at)) },
  { id: 'hasta', header: 'Hasta', cell: (tramo) => FORMATO.format(new Date(tramo.ends_at)) },
  { id: 'duracion', header: 'Duración', cell: (tramo) => `${String(tramo.duration_minutes)} min` },
  { id: 'acciones', header: 'Acciones', cell: (tramo) => <WithdrawSlotButton slotId={tramo.id} /> },
]

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
  const hoy = new Date().toISOString().slice(0, 10)
  const [rango, setRango] = useState<Rango>('todos')
  const [ancla, setAncla] = useState(hoy)

  const ventana = useMemo(() => calcularVentana(rango, ancla), [rango, ancla])
  const tramos = useQuery({
    queryKey: [...mySlotsQueryKey, ventana],
    queryFn: () => fetchMySlots(ventana.desde, ventana.hasta),
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Mi agenda" />

      <SlotForm />

      <SectionCard title="Tramos publicados">
        <AvailabilityRangeFilter
          rango={rango}
          ancla={ancla}
          onRangoChange={setRango}
          onAnclaChange={setAncla}
        />
        <DataTable
          columns={COLUMNAS}
          data={tramos.data?.items ?? []}
          isLoading={tramos.isPending}
          emptyMessage="Todavía no publicaste ningún tramo."
          getRowId={(tramo) => String(tramo.id)}
        />
      </SectionCard>
    </div>
  )
}
