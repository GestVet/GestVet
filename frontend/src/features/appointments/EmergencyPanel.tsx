import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { appointmentsQueryKey, openEmergency } from '../../api/appointments'
import { fetchMyPets, myPetsQueryKey } from '../../api/pets'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { errorMessage } from '../../services/api'

export default function EmergencyPanel() {
  const queryClient = useQueryClient()
  const mascotas = useQuery({ queryKey: myPetsQueryKey, queryFn: fetchMyPets })

  const emergencia = useMutation({
    mutationFn: (petId: number) => openEmergency({ pet_id: petId, description: '' }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: appointmentsQueryKey })
    },
  })

  const primera = mascotas.data?.items.find((mascota) => mascota.is_active)

  return (
    <section className="card">
      <h2>Emergencia</h2>
      <p className="muted">
        No se elige hora ni veterinario. El sistema asigna al que esté de guardia en este
        momento.
      </p>

      {emergencia.isError ? (
        <FormMessage tone="error">
          {errorMessage(emergencia.error, 'No se pudo abrir la emergencia.')}
        </FormMessage>
      ) : null}
      {emergencia.isSuccess ? (
        <FormMessage tone="ok">Emergencia abierta. Acercate a la clínica.</FormMessage>
      ) : null}

      <button
        type="button"
        className="btn btn-danger"
        disabled={emergencia.isPending || primera === undefined}
        onClick={() => {
          if (primera !== undefined) {
            emergencia.mutate(primera.id)
          }
        }}
      >
        <Icon name="emergencia" size={16} />
        <span>Abrir emergencia para {primera?.name ?? 'mi mascota'}</span>
      </button>
    </section>
  )
}
