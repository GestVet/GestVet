import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useRef, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'

import { openWalkInEmergency } from '../../api/appointments'
import { registerWalkInClient } from '../../api/directory'
import { registerPetForOwner } from '../../api/pets'
import type { AppointmentResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import { EMPTY_WALK_IN_EMERGENCY, walkInEmergencySchema } from './formValues'
import type { WalkInEmergencyFormValues } from './formValues'
import WalkInEmergencyFields from './WalkInEmergencyFields'
import WalkInEmergencySuccess from './WalkInEmergencySuccess'

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

  const { register, handleSubmit, formState, reset, control } = useForm<WalkInEmergencyFormValues>({
    resolver: zodResolver(walkInEmergencySchema),
    defaultValues: EMPTY_WALK_IN_EMERGENCY,
  })
  const especie = useWatch({ control, name: 'pet_species' })

  const abrir = useMutation({
    mutationFn: async (valores: WalkInEmergencyFormValues) => {
      if (clienteIdRef.current === null) {
        const cliente = await registerWalkInClient({
          first_name: valores.first_name,
          last_name: valores.last_name,
          document_id: valores.document_id,
          phone: valores.phone,
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
        description: valores.description,
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
    return <WalkInEmergencySuccess appointmentId={resultado.id} onRestart={empezarDeNuevo} />
  }

  return (
    <form
      noValidate
      className="flex flex-col gap-6"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          abrir.mutate(valores)
        }),
      )}
    >
      <WalkInEmergencyFields
        register={register}
        control={control}
        errors={formState.errors}
        species={especie}
      />

      {abrir.isError ? (
        <FormMessage tone="error">
          {errorMessage(abrir.error, 'No se pudo completar el alta exprés.')}
        </FormMessage>
      ) : null}

      <Button
        type="submit"
        variant="danger"
        size="lg"
        className="h-11 self-start px-5"
        disabled={abrir.isPending}
      >
        <Icon name="emergencia" size={16} />
        <span>{abrir.isPending ? 'Abriendo…' : 'Abrir emergencia'}</span>
      </Button>
    </form>
  )
}
