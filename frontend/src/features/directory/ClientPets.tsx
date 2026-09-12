import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { correctPetStatus, fetchPetsOfOwner, petsOfOwnerQueryKey } from '../../api/pets'
import FormMessage from '../../components/FormMessage'
import StatusBadge from '../../components/StatusBadge'
import { errorMessage } from '../../services/api'

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
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {items.map((mascota) => (
            <tr key={mascota.id}>
              <td>{mascota.name}</td>
              <td>{mascota.species}</td>
              <td>
                <StatusBadge
                  label={mascota.is_active ? 'Activa' : 'Fallecida'}
                  tone={mascota.is_active ? 'completed' : undefined}
                />
              </td>
              <td>
                <button
                  type="button"
                  className="btn btn-plain"
                  disabled={corregir.isPending}
                  onClick={() => {
                    pedirCorreccion(mascota.id, !mascota.is_active)
                  }}
                >
                  Corregir a {mascota.is_active ? 'fallecida' : 'activa'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
