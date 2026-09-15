import { keepPreviousData, useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import {
  downloadServiceConsumptionPdf,
  fetchServiceConsumption,
  serviceConsumptionQueryKey,
} from '../../api/insights'
import type { ServiceConsumptionResponse } from '../../api/types'
import BarChart from '../../components/charts/BarChart'
import DataTable, { type DataColumn } from '../../components/DataTable'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SectionCard from '../../components/SectionCard'
import { guardarArchivo } from '../../services/descargas'
import { errorMessage } from '../../services/api'
import { instanteEnClinica, sumarDias } from '../../services/clinicTime'
import { Button } from '../../components/ui/button'
import ServiceConsumptionFilters from './ServiceConsumptionFilters'

const COLUMNAS: readonly DataColumn<ServiceConsumptionResponse>[] = [
  { id: 'servicio', header: 'Servicio', cell: (item) => item.name },
  { id: 'precio', header: 'Precio', cell: (item) => `S/ ${item.price}` },
  { id: 'veces', header: 'Veces', cell: (item) => String(item.appointment_count) },
  { id: 'ingreso', header: 'Ingreso estimado', cell: (item) => `S/ ${item.estimated_revenue}` },
]

/** Del inicio de `desde` al final de `hasta`, en la hora de la clínica. */
function ventanaDeFechas(desde: string, hasta: string, estado: string) {
  return {
    starts_after: desde === '' ? undefined : instanteEnClinica(desde),
    ends_before: hasta === '' ? undefined : instanteEnClinica(sumarDias(hasta, 1)),
    status: estado === '' ? undefined : estado,
  }
}

export default function ServiceConsumptionSection() {
  const [estado, setEstado] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const filtro = ventanaDeFechas(desde, hasta, estado)

  const reporte = useQuery({
    queryKey: serviceConsumptionQueryKey(filtro),
    queryFn: () => fetchServiceConsumption(filtro),
    placeholderData: keepPreviousData,
  })

  const pdf = useMutation({
    mutationFn: async () => {
      const blob = await downloadServiceConsumptionPdf(filtro)
      guardarArchivo(blob, 'servicios-mas-consumidos.pdf')
    },
  })

  const items = reporte.data?.items ?? []
  const grafico = items.map((item) => ({
    label: item.name,
    value: item.appointment_count,
    color: 'var(--chart-1)',
  }))

  return (
    <SectionCard
      title="Servicios más consumidos"
      description="Cuántas citas tuvo cada servicio, sin datos de clientes. Cambiá el estado o el rango para actualizar la tabla y el gráfico."
      actions={
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={pdf.isPending}
          onClick={() => {
            pdf.mutate()
          }}
        >
          <Icon name="descargar" size={16} />
          <span>{pdf.isPending ? 'Generando…' : 'Descargar PDF'}</span>
        </Button>
      }
    >
      <div className="flex flex-col gap-4">
        <ServiceConsumptionFilters
          estado={estado}
          desde={desde}
          hasta={hasta}
          onEstadoChange={setEstado}
          onDesdeChange={setDesde}
          onHastaChange={setHasta}
        />
        {pdf.isError ? (
          <FormMessage tone="error">
            {errorMessage(pdf.error, 'No se pudo generar el PDF.')}
          </FormMessage>
        ) : null}
        <DataTable
          columns={COLUMNAS}
          data={items}
          isLoading={reporte.isPending}
          emptyMessage="No hay citas en el rango elegido."
          getRowId={(item) => String(item.appointment_type_id)}
          pageSize={10}
        />
        <BarChart
          title="Servicios más consumidos"
          data={grafico}
          emptyMessage="No hay servicios para graficar."
          horizontal
        />
      </div>
    </SectionCard>
  )
}
