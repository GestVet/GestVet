import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { fetchMyPets, myPetsQueryKey } from '../../api/pets'
import type { PetResponse } from '../../api/types'
import DataTable, { type DataColumn } from '../../components/DataTable'
import FormDialog from '../../components/FormDialog'
import Icon from '../../components/Icon'
import PageHeader from '../../components/PageHeader'
import SectionCard from '../../components/SectionCard'
import StatusBadge from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
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
  const [registrando, setRegistrando] = useState(false)
  const cerrar = () => {
    setRegistrando(false)
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Mis mascotas"
        description="Con una mascota registrada ya puedes reservarle citas."
        actions={
          <Button
            type="button"
            size="lg"
            className="h-10 px-4"
            onClick={() => {
              setRegistrando(true)
            }}
          >
            <Icon name="agregar" size={16} />
            <span>Registrar mascota</span>
          </Button>
        }
      />

      <FormDialog
        open={registrando}
        onOpenChange={setRegistrando}
        title="Registrar una mascota"
        description="El resto de la ficha, como el color o el microchip, lo completas después desde sus detalles."
        size="lg"
      >
        <PetForm onDone={cerrar} />
      </FormDialog>

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
