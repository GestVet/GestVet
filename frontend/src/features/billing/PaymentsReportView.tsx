import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import {
  fetchPaymentReport,
  fetchPayments,
  paymentReportQueryKey,
  paymentsQueryKey,
} from '../../api/payments'
import DataTable, { type DataColumn } from '../../components/DataTable'
import PageHeader from '../../components/PageHeader'
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

export default function PaymentsReportView() {
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')

  const filtro = {
    starts_after: desde === '' ? undefined : new Date(desde).toISOString(),
    ends_before: hasta === '' ? undefined : new Date(hasta).toISOString(),
  }

  const reporte = useQuery({
    queryKey: paymentReportQueryKey(filtro),
    queryFn: () => fetchPaymentReport(filtro),
  })
  const pagos = useQuery({
    queryKey: paymentsQueryKey(filtro),
    queryFn: () => fetchPayments(filtro),
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Pagos" />

      <SectionCard title="Resumen por medio de pago">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-2">
            <Label htmlFor="reporte-desde">Desde</Label>
            <Input
              id="reporte-desde"
              type="date"
              className="h-10"
              value={desde}
              onChange={(evento) => {
                setDesde(evento.target.value)
              }}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="reporte-hasta">Hasta</Label>
            <Input
              id="reporte-hasta"
              type="date"
              className="h-10"
              value={hasta}
              onChange={(evento) => {
                setHasta(evento.target.value)
              }}
            />
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
