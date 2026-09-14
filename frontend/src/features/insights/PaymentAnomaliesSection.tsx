import { useQuery } from '@tanstack/react-query'

import { fetchPaymentAnomalies, paymentAnomaliesQueryKey } from '../../api/insights'
import DataTable, { type DataColumn } from '../../components/DataTable'
import SectionCard from '../../components/SectionCard'

type Anomalia = Awaited<ReturnType<typeof fetchPaymentAnomalies>>['items'][number]

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

const COLUMNAS: readonly DataColumn<Anomalia>[] = [
  { id: 'pago', header: 'Pago', cell: (item) => `#${String(item.payment_id)}` },
  { id: 'cita', header: 'Cita', cell: (item) => `#${String(item.appointment_id)}` },
  { id: 'tipo', header: 'Tipo', cell: (item) => item.appointment_type_label },
  { id: 'monto', header: 'Monto', cell: (item) => `S/ ${item.amount}` },
  { id: 'tipico', header: 'Típico', cell: (item) => `S/ ${item.typical_amount}` },
  { id: 'cuando', header: 'Cuándo', cell: (item) => FORMATO.format(new Date(item.paid_at)) },
]

export default function PaymentAnomaliesSection() {
  const anomalias = useQuery({
    queryKey: paymentAnomaliesQueryKey,
    queryFn: fetchPaymentAnomalies,
  })

  return (
    <SectionCard
      collapsible
      scrollable
      title="Pagos fuera de lo típico"
      description="Pagos de los últimos 30 días cuyo monto se aleja bastante del promedio de su tipo de cita. Las emergencias no entran, porque su precio varía por diseño."
    >
      <DataTable
        columns={COLUMNAS}
        data={anomalias.data?.items ?? []}
        isLoading={anomalias.isPending}
        emptyMessage="No hay pagos fuera de lo típico."
        getRowId={(item) => String(item.payment_id)}
      />
    </SectionCard>
  )
}
