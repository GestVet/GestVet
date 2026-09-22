import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'

import type { AppointmentResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import { EMPTY_WALK_IN_EMERGENCY, walkInEmergencySchema } from './formValues'
import type { WalkInEmergencyFormValues } from './formValues'
import { useWalkInEmergency } from './useWalkInEmergency'
import WalkInEmergencyFields from './WalkInEmergencyFields'
import WalkInEmergencySuccess from './WalkInEmergencySuccess'
import WalkInRiskConsentFields from './WalkInRiskConsentFields'

/** Alta exprés: cliente, mascota, aceptación del riesgo y emergencia, en una sola acción. */
export default function WalkInEmergencyForm() {
  const [resultado, setResultado] = useState<AppointmentResponse | null>(null)
  const { plantilla, abrir, olvidar } = useWalkInEmergency(setResultado)

  const { register, handleSubmit, formState, reset, control, setValue } = useForm<WalkInEmergencyFormValues>({
    resolver: zodResolver(walkInEmergencySchema),
    defaultValues: EMPTY_WALK_IN_EMERGENCY,
  })
  const especie = useWatch({ control, name: 'pet_species' })

  const empezarDeNuevo = () => {
    olvidar()
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
        setValue={setValue}
      />

      <WalkInRiskConsentFields
        register={register}
        control={control}
        errors={formState.errors}
        setValue={setValue}
        signerEdited={formState.dirtyFields.signer_name === true}
        template={plantilla.data}
        templateError={plantilla.isError}
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
        disabled={abrir.isPending || plantilla.data === undefined}
      >
        <Icon name="emergencia" size={16} />
        <span>{abrir.isPending ? 'Abriendo…' : 'Abrir emergencia'}</span>
      </Button>
    </form>
  )
}
