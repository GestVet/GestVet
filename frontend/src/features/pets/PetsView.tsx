import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { changePetStatus, fetchMyPets, myPetsQueryKey } from '../../api/pets'
import StatusBadge from '../../components/StatusBadge'
import TableShell from '../../components/TableShell'
import PetForm from './PetForm'

const COLUMNAS = ['Nombre', 'Especie', 'Raza', 'Edad', 'Estado', 'Acciones'] as const

export default function PetsView() {
  const queryClient = useQueryClient()
  const mascotas = useQuery({ queryKey: myPetsQueryKey, queryFn: fetchMyPets })

  const cambiarEstado = useMutation({
    mutationFn: ({ id, activa }: { id: number; activa: boolean }) => changePetStatus(id, activa),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: myPetsQueryKey })
    },
  })

  const items = mascotas.data?.items ?? []

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Mis mascotas</h1>
      </div>

      <PetForm />

      <section className="card">
        <h2>Registradas</h2>
        <TableShell
          columns={COLUMNAS}
          isLoading={mascotas.isPending}
          isEmpty={items.length === 0}
          emptyMessage="Todavía no registraste ninguna mascota."
        >
          {items.map((mascota) => (
            <tr key={mascota.id}>
              <td>{mascota.name}</td>
              <td>{mascota.species}</td>
              <td>{mascota.breed}</td>
              <td>{mascota.age_in_years} años</td>
              <td>
                <StatusBadge
                  label={mascota.is_active ? 'Activa' : 'Dada de baja'}
                  tone={mascota.is_active ? 'completed' : undefined}
                />
              </td>
              <td>
                <button
                  type="button"
                  className={mascota.is_active ? 'btn btn-plain' : 'btn btn-green'}
                  disabled={cambiarEstado.isPending}
                  onClick={() => {
                    cambiarEstado.mutate({ id: mascota.id, activa: !mascota.is_active })
                  }}
                >
                  {mascota.is_active ? 'Dar de baja' : 'Reactivar'}
                </button>
              </td>
            </tr>
          ))}
        </TableShell>
      </section>
    </div>
  )
}
