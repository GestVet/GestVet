import { useQuery } from '@tanstack/react-query'

import { complaintsQueryKey, fetchComplaints } from '../../api/complaints'
import DataTable, { type DataColumn } from '../../components/DataTable'
import PageHeader from '../../components/PageHeader'

type Reclamo = Awaited<ReturnType<typeof fetchComplaints>>['items'][number]

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

const COLUMNAS: readonly DataColumn<Reclamo>[] = [
  { id: 'fecha', header: 'Fecha', cell: (reclamo) => FORMATO.format(new Date(reclamo.created_at)) },
  { id: 'cliente', header: 'Cliente', cell: (reclamo) => `#${String(reclamo.client_id)}` },
  {
    id: 'veterinario',
    header: 'Veterinario',
    cell: (reclamo) => `#${String(reclamo.veterinarian_id)}`,
  },
  { id: 'cita', header: 'Cita', cell: (reclamo) => `#${String(reclamo.appointment_id)}` },
  {
    id: 'descripcion',
    header: 'Descripción',
    className: 'min-w-64 whitespace-normal',
    cell: (reclamo) => reclamo.description,
  },
  {
    id: 'evidencia',
    header: 'Evidencia',
    cell: (reclamo) =>
      reclamo.evidence.length === 0 ? (
        <span className="text-muted-foreground">Sin evidencia</span>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-1 p-0">
          {reclamo.evidence.map((archivo) => (
            <li key={archivo.id}>
              <a
                href={archivo.url}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-primary underline underline-offset-4"
              >
                {archivo.filename}
              </a>
            </li>
          ))}
        </ul>
      ),
  },
]

export default function ComplaintsView() {
  const reclamos = useQuery({ queryKey: complaintsQueryKey, queryFn: fetchComplaints })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Reclamos"
        description="Lo que presentan los clientes sobre la atención de una cita puntual."
      />
      <DataTable
        columns={COLUMNAS}
        data={reclamos.data?.items ?? []}
        isLoading={reclamos.isPending}
        emptyMessage="Todavía no hay reclamos registrados."
        getRowId={(reclamo) => String(reclamo.id)}
      />
    </div>
  )
}
