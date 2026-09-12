import { useQuery } from '@tanstack/react-query'

import { complaintsQueryKey, fetchComplaints } from '../../api/complaints'
import TableShell from '../../components/TableShell'

const COLUMNAS = ['Fecha', 'Cliente', 'Veterinario', 'Cita', 'Descripción', 'Evidencia'] as const

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

export default function ComplaintsView() {
  const reclamos = useQuery({ queryKey: complaintsQueryKey, queryFn: fetchComplaints })
  const items = reclamos.data?.items ?? []

  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Reclamos</h1>
          <p className="muted">
            Lo que presentan los clientes sobre la atención de una cita puntual.
          </p>
        </div>
      </div>

      <section className="card">
        <TableShell
          columns={COLUMNAS}
          isLoading={reclamos.isPending}
          isEmpty={items.length === 0}
          emptyMessage="Todavía no hay reclamos registrados."
        >
          {items.map((reclamo) => (
            <tr key={reclamo.id}>
              <td>{FORMATO.format(new Date(reclamo.created_at))}</td>
              <td>#{reclamo.client_id}</td>
              <td>#{reclamo.veterinarian_id}</td>
              <td>#{reclamo.appointment_id}</td>
              <td>{reclamo.description}</td>
              <td>
                {reclamo.evidence.length === 0 ? (
                  <span className="muted">Sin evidencia</span>
                ) : (
                  <ul>
                    {reclamo.evidence.map((archivo) => (
                      <li key={archivo.id}>
                        <a href={archivo.url} target="_blank" rel="noreferrer">
                          {archivo.filename}
                        </a>
                      </li>
                    ))}
                  </ul>
                )}
              </td>
            </tr>
          ))}
        </TableShell>
      </section>
    </div>
  )
}
