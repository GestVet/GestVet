import { useQuery } from '@tanstack/react-query'

import { fetchPetsOfOwner, petsOfOwnerQueryKey } from '../../api/pets'
import type { PetResponse } from '../../api/types'
import DataTable, { type DataColumn } from '../../components/DataTable'
import StatusBadge from '../../components/StatusBadge'
import ClientPetActions from './ClientPetActions'
import ClientPetDetails from './ClientPetDetails'

const COLUMNAS: readonly DataColumn<PetResponse>[] = [
  { id: 'nombre', header: 'Nombre', cell: (mascota) => mascota.name },
  { id: 'especie', header: 'Especie', cell: (mascota) => mascota.species },
  {
    id: 'peso',
    header: 'Peso',
    cell: (mascota) => (mascota.weight_kg ? `${mascota.weight_kg} kg` : '—'),
  },
  {
    id: 'altura',
    header: 'Altura',
    cell: (mascota) => (mascota.height_cm ? `${mascota.height_cm} cm` : '—'),
  },
  {
    id: 'estado',
    header: 'Estado',
    cell: (mascota) => (
      <StatusBadge
        label={mascota.is_active ? 'Activa' : 'Fallecida'}
        tone={mascota.is_active ? 'completed' : undefined}
      />
    ),
  },
  {
    id: 'acciones',
    header: 'Acciones',
    cell: (mascota, fila) => (
      <ClientPetActions
        mascota={mascota}
        isExpanded={fila.isExpanded}
        onToggle={fila.toggleExpanded}
      />
    ),
  },
]

interface ClientPetsProps {
  readonly ownerId: number
}

/** Mascotas de un cliente, vistas por el personal de la clínica. */
export default function ClientPets({ ownerId }: ClientPetsProps) {
  const mascotas = useQuery({
    queryKey: petsOfOwnerQueryKey(ownerId),
    queryFn: () => fetchPetsOfOwner(ownerId),
  })

  return (
    <DataTable
      columns={COLUMNAS}
      data={mascotas.data?.items ?? []}
      isLoading={mascotas.isPending}
      emptyMessage="Este cliente todavía no registró mascotas."
      getRowId={(mascota) => String(mascota.id)}
      renderExpanded={(mascota) => <ClientPetDetails mascota={mascota} />}
    />
  )
}
