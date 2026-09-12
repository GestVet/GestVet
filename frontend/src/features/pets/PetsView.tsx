import { useQuery } from '@tanstack/react-query'

import { fetchMyPets, myPetsQueryKey } from '../../api/pets'
import type { PetResponse } from '../../api/types'
import DataTable, { type DataColumn } from '../../components/DataTable'
import PageHeader from '../../components/PageHeader'
import SectionCard from '../../components/SectionCard'
import StatusBadge from '../../components/StatusBadge'
import PetActions from './PetActions'
import PetDetails from './PetDetails'
import PetForm from './PetForm'

const COLUMNAS: readonly DataColumn<PetResponse>[] = [
  { id: 'nombre', header: 'Nombre', cell: (mascota) => mascota.name },
  { id: 'especie', header: 'Especie', cell: (mascota) => mascota.species },
  { id: 'raza', header: 'Raza', cell: (mascota) => mascota.breed },
  { id: 'edad', header: 'Edad', cell: (mascota) => `${String(mascota.age_in_years)} años` },
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
      <PetActions mascota={mascota} isExpanded={fila.isExpanded} onToggle={fila.toggleExpanded} />
    ),
  },
]

export default function PetsView() {
  const mascotas = useQuery({ queryKey: myPetsQueryKey, queryFn: fetchMyPets })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Mis mascotas" />

      <PetForm />

      <SectionCard title="Registradas">
        <DataTable
          columns={COLUMNAS}
          data={mascotas.data?.items ?? []}
          isLoading={mascotas.isPending}
          emptyMessage="Todavía no registraste ninguna mascota."
          getRowId={(mascota) => String(mascota.id)}
          renderExpanded={(mascota) => <PetDetails mascota={mascota} />}
        />
      </SectionCard>
    </div>
  )
}
