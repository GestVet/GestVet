import { useQuery } from '@tanstack/react-query'

import { fetchVeterinarianAlerts, veterinarianAlertsQueryKey } from '../../api/insights'
import TableShell from '../../components/TableShell'

const COLUMNAS = ['Veterinario', 'Reseñas bajas (60 días)', 'Reclamos (60 días)'] as const

export default function VeterinarianAlertsSection() {
  const alertas = useQuery({
    queryKey: veterinarianAlertsQueryKey,
    queryFn: fetchVeterinarianAlerts,
  })
  const items = alertas.data?.items ?? []

  return (
    <section className="card">
      <h2>Veterinarios a seguir de cerca</h2>
      <p className="muted">
        Tres o más reseñas de 1-2 estrellas, o dos o más reclamos, en los últimos 60 días.
      </p>
      <TableShell
        columns={COLUMNAS}
        isLoading={alertas.isPending}
        isEmpty={items.length === 0}
        emptyMessage="Ningún veterinario está en ese caso ahora mismo."
      >
        {items.map((item) => (
          <tr key={item.veterinarian_id}>
            <td>{item.veterinarian_name}</td>
            <td>{item.low_rating_count}</td>
            <td>{item.complaint_count}</td>
          </tr>
        ))}
      </TableShell>
    </section>
  )
}
