import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useRef, useState } from 'react'
import { useForm } from 'react-hook-form'

import { openWalkInEmergency } from '../../api/appointments'
import { registerWalkInClient } from '../../api/directory'
import { registerPetForOwner } from '../../api/pets'
import type { AppointmentResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import { EMPTY_WALK_IN_EMERGENCY, walkInEmergencySchema } from './formValues'
import type { WalkInEmergencyFormValues } from './formValues'
import WalkInEmergencyFields from './WalkInEmergencyFields'

/**
 * Alta exprés: cliente + mascota + emergencia, en una sola acción.
 *
 * Son tres llamadas seguidas porque cada módulo es dueño de su propia
 * escritura — no hay una transacción única detrás. Si una llamada intermedia
 * falla, los identificadores ya obtenidos quedan guardados acá, así que
 * reintentar no vuelve a crear lo que ya se creó.
 */
export default function WalkInEmergencyForm() {
  const [resultado, setResultado] = useState<AppointmentResponse | null>(null)
  const clienteIdRef = useRef<number | null>(null)
  const mascotaIdRef = useRef<number | null>(null)

  const { register, handleSubmit, formState, reset } = useForm<WalkInEmergencyFormValues>({
    resolver: zodResolver(walkInEmergencySchema),
    defaultValues: EMPTY_WALK_IN_EMERGENCY,
  })

  const abrir = useMutation({
    mutationFn: async (valores: WalkInEmergencyFormValues) => {
      if (clienteIdRef.current === null) {
        const cliente = await registerWalkInClient({
          first_name: valores.first_name,
          last_name: valores.last_name,
          document_id: valores.document_id,
          phone: valores.phone ?? '',
        })
        clienteIdRef.current = cliente.id
      }
      if (mascotaIdRef.current === null) {
        const mascota = await registerPetForOwner({
          owner_id: clienteIdRef.current,
          name: valores.pet_name,
          species: valores.pet_species,
        })
        mascotaIdRef.current = mascota.id
      }
      return openWalkInEmergency({
        client_id: clienteIdRef.current,
        pet_id: mascotaIdRef.current,
        description: valores.description ?? '',
      })
    },
    onSuccess: setResultado,
  })

  const empezarDeNuevo = () => {
    clienteIdRef.current = null
    mascotaIdRef.current = null
    setResultado(null)
    reset(EMPTY_WALK_IN_EMERGENCY)
  }

  if (resultado) {
    return (
      <div className="stack">
        <FormMessage tone="ok">
          Emergencia abierta (#{resultado.id}). Quedó asignada automáticamente a un veterinario
          disponible. El cliente y la mascota ya quedaron registrados — el personal puede
          completar el correo real desde la ficha del cliente cuando haya tiempo.
        </FormMessage>
        <button type="button" className="btn btn-plain" onClick={empezarDeNuevo}>
          Registrar otra emergencia
        </button>
      </div>
    )
  }

  return (
    <form
      className="form"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          abrir.mutate(valores)
        }),
      )}
    >
      <WalkInEmergencyFields register={register} errors={formState.errors} />

      {abrir.isError ? (
        <FormMessage tone="error">
          {errorMessage(abrir.error, 'No se pudo completar el alta exprés.')}
        </FormMessage>
      ) : null}

      <button type="submit" className="btn btn-danger" disabled={abrir.isPending}>
        <span>{abrir.isPending ? 'Abriendo…' : 'Abrir emergencia'}</span>
      </button>
    </form>
  )
}
