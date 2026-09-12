import { useQuery } from '@tanstack/react-query'

import { careRemindersQueryKey, fetchCareReminders } from '../../api/insights'
import TableShell from '../../components/TableShell'

const COLUMNAS = ['Mascota', 'Dueño', 'Motivo', 'Última vez'] as const
const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium' })

export default function CareRemindersSection() {
  const recordatorios = useQuery({
    queryKey: careRemindersQueryKey,
    queryFn: fetchCareReminders,
  })
  const items = recordatorios.data?.items ?? []

  return (
    <section className="card">
      <h2>Cuidado vencido</h2>
      <p className="muted">
        Mascotas sin vacuna hace más de un año o sin control hace más de medio año.
      </p>
      <TableShell
        columns={COLUMNAS}
        isLoading={recordatorios.isPending}
        isEmpty={items.length === 0}
        emptyMessage="No hay recordatorios pendientes."
      >
        {items.map((item, index) => (
          <tr key={`${String(item.pet_id)}-${item.reason_label}-${String(index)}`}>
            <td>{item.pet_name}</td>
            <td>{item.owner_name}</td>
            <td>{item.reason_label}</td>
            <td>
              {item.last_occurred_at ? FORMATO.format(new Date(item.last_occurred_at)) : 'Nunca'}
            </td>
          </tr>
        ))}
      </TableShell>
    </section>
  )
}
