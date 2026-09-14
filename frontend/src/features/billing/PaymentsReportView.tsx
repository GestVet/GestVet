import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import {
  fetchPaymentReport,
  fetchPayments,
  paymentReportQueryKey,
  paymentsQueryKey,
} from '../../api/payments'
import DataTable, { type DataColumn } from '../../components/DataTable'
import FieldIcon from '../../components/FieldIcon'
import PageHeader from '../../components/PageHeader'
import { instanteEnClinica, sumarDias } from '../../services/clinicTime'
import SectionCard from '../../components/SectionCard'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import PaymentReportSummary from './PaymentReportSummary'

type Pago = Awaited<ReturnType<typeof fetchPayments>>['items'][number]

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

const COLUMNAS: readonly DataColumn<Pago>[] = [
  { id: 'fecha', header: 'Fecha', cell: (pago) => FORMATO.format(new Date(pago.paid_at)) },
  { id: 'cita', header: 'Cita', cell: (pago) => `#${String(pago.appointment_id)}` },
  { id: 'monto', header: 'Monto', cell: (pago) => `S/ ${pago.amount}` },
  { id: 'medio', header: 'Medio', cell: (pago) => pago.method_label },
  { id: 'referencia', header: 'Referencia', cell: (pago) => pago.reference || '—' },
  {
    id: 'estado',
    header: 'Estado',
    className: 'whitespace-normal',
    cell: (pago) =>
      pago.is_voided ? (
        <span className="text-muted-foreground">Anulado: {pago.void_reason}</span>
      ) : (
        'Vigente'
      ),
  },
]

/** Del inicio de `desde` al final de `hasta`, en la hora de la clínica. */
function ventanaDeFechas(desde: string, hasta: string) {
  return {
    starts_after: desde === '' ? undefined : instanteEnClinica(desde),
    ends_before: hasta === '' ? undefined : instanteEnClinica(sumarDias(hasta, 1)),
  }
}

function limite(fecha: string): string | undefined {
  return fecha === '' ? undefined : fecha
}

export default function PaymentsReportView() {
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')

  const filtro = ventanaDeFechas(desde, hasta)

  // Con las fechas cambiando, el resumen y la tabla conservan lo anterior
  // hasta que llega el rango nuevo, en vez de vaciarse.
  const reporte = useQuery({
    queryKey: paymentReportQueryKey(filtro),
    queryFn: () => fetchPaymentReport(filtro),
    placeholderData: keepPreviousData,
  })
  const pagos = useQuery({
    queryKey: paymentsQueryKey(filtro),
    queryFn: () => fetchPayments(filtro),
    placeholderData: keepPreviousData,
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Pagos" />

      <SectionCard title="Resumen por medio de pago">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-2">
            <Label htmlFor="reporte-desde">Desde</Label>
            <FieldIcon icon="fecha">
            <Input
              id="reporte-desde"
              type="date"
              className="h-10"
              max={limite(hasta)}
              value={desde}
              onChange={(evento) => {
                setDesde(evento.target.value)
              }}
            />
            </FieldIcon>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="reporte-hasta">Hasta</Label>
            <FieldIcon icon="fecha">
            <Input
              id="reporte-hasta"
              type="date"
              className="h-10"
              min={limite(desde)}
              value={hasta}
              onChange={(evento) => {
                setHasta(evento.target.value)
              }}
            />
            </FieldIcon>
          </div>
        </div>

        <PaymentReportSummary
          isLoading={reporte.isPending}
          items={reporte.data?.items ?? []}
          grandTotal={reporte.data?.grand_total ?? '0'}
        />
      </SectionCard>

      <SectionCard title="Pagos">
        <DataTable
          columns={COLUMNAS}
          data={pagos.data?.items ?? []}
          isLoading={pagos.isPending}
          emptyMessage="No hay pagos para mostrar."
          getRowId={(pago) => String(pago.id)}
        />
      </SectionCard>
    </div>
  )
}
