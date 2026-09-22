import { type Control, Controller, type FieldErrors, type UseFormRegister } from 'react-hook-form'

import type { ConsentTemplateResponse, PetResponse } from '../../api/types'
import ConsentCheckboxField from '../../components/ConsentCheckboxField'
import ConsentText from '../../components/ConsentText'
import SelectField from '../../components/SelectField'
import TextareaField from '../../components/TextareaField'
import TextField from '../../components/TextField'
import { NativeSelectOption } from '../../components/ui/native-select'
import { MAX_FIRMA } from '../../services/fieldRules'
import type { EmergencyFormInput } from './emergencySchema'

interface EmergencyFormFieldsProps {
  readonly register: UseFormRegister<EmergencyFormInput>
  readonly control: Control<EmergencyFormInput>
  readonly errors: FieldErrors<EmergencyFormInput>
  readonly pets: readonly PetResponse[]
  readonly template: ConsentTemplateResponse | undefined
  readonly templateError: boolean
}

/** Los campos de la emergencia y de la aceptación del riesgo, separados del envío. */
export default function EmergencyFormFields({
  register,
  control,
  errors,
  pets,
  template,
  templateError,
}: EmergencyFormFieldsProps) {
  return (
    <>
      <SelectField
        id="emergencia-mascota"
        label="Mascota"
        icon="mascota"
        placeholder={pets.length > 1 ? 'Elige la mascota' : undefined}
        field={register('pet_id')}
        error={errors.pet_id?.message}
      >
        {pets.map((mascota) => (
          <NativeSelectOption key={mascota.id} value={String(mascota.id)}>
            {mascota.name}
          </NativeSelectOption>
        ))}
      </SelectField>

      <TextareaField
        id="emergencia-descripcion"
        label="¿Qué le pasa? (opcional)"
        placeholder="Comió algo tóxico y está vomitando"
        icon="emergencia"
        rows={2}
        field={register('description')}
        error={errors.description?.message}
      />

      <ConsentText id="emergencia-consentimiento" template={template} isError={templateError} />

      <Controller
        control={control}
        name="accepted"
        render={({ field }) => (
          <ConsentCheckboxField
            id="emergencia-acepto"
            label="Leí y acepto el riesgo descrito"
            checked={field.value}
            onCheckedChange={field.onChange}
            onBlur={field.onBlur}
            inputRef={field.ref}
            error={errors.accepted?.message}
          />
        )}
      />

      <TextField
        id="emergencia-firma"
        label="Nombre completo de quien firma"
        icon="perfil"
        autoComplete="name"
        maxLength={MAX_FIRMA}
        field={register('signer_name')}
        error={errors.signer_name?.message}
      />
    </>
  )
}
