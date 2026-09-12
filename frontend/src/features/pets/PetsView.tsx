import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { changePetStatus, fetchMyPets, myPetsQueryKey } from '../../api/pets'
import FormMessage from '../../components/FormMessage'
import TableShell from '../../components/TableShell'
import { errorMessage } from '../../services/api'
import PetForm from './PetForm'
import PetRow from './PetRow'

const COLUMNAS = ['Nombre', 'Especie', 'Raza', 'Edad', 'Peso', 'Altura', 'Estado', 'Acciones'] as const

export default function PetsView() {
  const queryClient = useQueryClient()
  const mascotas = useQuery({ queryKey: myPetsQueryKey, queryFn: fetchMyPets })

  const darDeBaja = useMutation({
    mutationFn: (id: number) => changePetStatus(id, false),
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
        {darDeBaja.isError ? (
          <FormMessage tone="error">
            {errorMessage(darDeBaja.error, 'No se pudo actualizar el estado.')}
          </FormMessage>
        ) : null}
        <TableShell
          columns={COLUMNAS}
          isLoading={mascotas.isPending}
          isEmpty={items.length === 0}
          emptyMessage="Todavía no registraste ninguna mascota."
        >
          {items.map((mascota) => (
            <PetRow
              key={mascota.id}
              mascota={mascota}
              dandoDeBaja={darDeBaja.isPending}
              onDarDeBaja={() => {
                if (
                  window.confirm(
                    `¿Confirmás que ${mascota.name} falleció? Esta acción no se puede deshacer; solo el personal de la clínica puede corregirla si fue un error.`,
                  )
                ) {
                  darDeBaja.mutate(mascota.id)
                }
              }}
            />
          ))}
        </TableShell>
      </section>
    </div>
  )
}
