import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { correctPetStatus, fetchPetsOfOwner, petsOfOwnerQueryKey } from '../../api/pets'
import FormMessage from '../../components/FormMessage'
import { errorMessage } from '../../services/api'
import ClientPetRow from './ClientPetRow'

interface ClientPetsProps {
  readonly ownerId: number
}

/**
 * Mascotas de un cliente, con la corrección de estado que le corresponde al
 * personal de la clínica.
 *
 * Distinta de la baja que hace el dueño: acá se puede volver de "fallecida" a
 * "activa", porque es para deshacer un error de carga, no para revivir una
 * mascota. El motivo queda en la bitácora.
 */
export default function ClientPets({ ownerId }: ClientPetsProps) {
  const queryClient = useQueryClient()
  const queryKey = petsOfOwnerQueryKey(ownerId)
  const mascotas = useQuery({ queryKey, queryFn: () => fetchPetsOfOwner(ownerId) })

  const corregir = useMutation({
    mutationFn: ({ id, activa, motivo }: { id: number; activa: boolean; motivo: string }) =>
      correctPetStatus(id, activa, motivo),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey })
    },
  })

  const pedirCorreccion = (id: number, activa: boolean) => {
    const motivo = window.prompt(
      `¿Por qué se corrige el estado a "${activa ? 'activa' : 'fallecida'}"? Solo para un error de carga.`,
    )
    if (motivo !== null && motivo.trim() !== '') {
      corregir.mutate({ id, activa, motivo })
    }
  }

  const items = mascotas.data?.items ?? []

  if (mascotas.isPending) {
    return <p className="empty">Cargando…</p>
  }
  if (items.length === 0) {
    return <p className="empty">Este cliente todavía no registró mascotas.</p>
  }

  return (
    <div className="stack">
      {corregir.isError ? (
        <FormMessage tone="error">
          {errorMessage(corregir.error, 'No se pudo corregir el estado.')}
        </FormMessage>
      ) : null}
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Especie</th>
            <th>Peso</th>
            <th>Altura</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {items.map((mascota) => (
            <ClientPetRow
              key={mascota.id}
              mascota={mascota}
              corrigiendo={corregir.isPending}
              onCorregir={() => {
                pedirCorreccion(mascota.id, !mascota.is_active)
              }}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}
