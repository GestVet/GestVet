import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import type { AppointmentResponse, PetResponse } from '../../api/types'
import DialogFormActions from '../../components/DialogFormActions'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import EmergencyFormFields from './EmergencyFormFields'
import {
  type EmergencyFormInput,
  type EmergencyFormValues,
  emergencySchema,
} from './emergencySchema'
import { useSignedEmergency } from './useSignedEmergency'

interface EmergencyFormProps {
  readonly pets: readonly PetResponse[]
  readonly signerName: string
  readonly onCancel: () => void
  readonly onOpened: (cita: AppointmentResponse) => void
}

/** La mascota, qué le pasa y la aceptación del riesgo, en un solo envío. */
export default function EmergencyForm({ pets, signerName, onCancel, onOpened }: EmergencyFormProps) {
  const { plantilla, abrir, firmado } = useSignedEmergency(onOpened)
  const { register, control, handleSubmit, formState } = useForm<
    EmergencyFormInput,
    unknown,
    EmergencyFormValues
  >({
    resolver: zodResolver(emergencySchema),
    defaultValues: {
      pet_id: pets.length === 1 ? String(pets[0]?.id) : '',
      description: '',
      accepted: false,
      signer_name: signerName,
    },
  })

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          abrir.mutate(valores)
        }),
      )}
    >
      <EmergencyFormFields
        register={register}
        control={control}
        errors={formState.errors}
        pets={pets}
        template={plantilla.data}
        templateError={plantilla.isError}
      />

      {abrir.isError ? (
        <FormMessage tone="error">
          {errorMessage(abrir.error, 'No se pudo abrir la emergencia.')}
          {firmado ? ' Tu aceptación ya quedó registrada: puedes reintentar sin volver a firmar.' : ''}
        </FormMessage>
      ) : null}

      <DialogFormActions>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
        <Button
          type="submit"
          variant="danger"
          disabled={abrir.isPending || plantilla.data === undefined}
        >
          <Icon name="emergencia" size={16} />
          <span>{abrir.isPending ? 'Abriendo…' : 'Aceptar y abrir emergencia'}</span>
        </Button>
      </DialogFormActions>
    </form>
  )
}
