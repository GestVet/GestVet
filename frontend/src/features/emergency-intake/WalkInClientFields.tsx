import {
  type Control,
  type FieldErrors,
  type UseFormRegister,
  type UseFormSetValue,
  useWatch,
} from 'react-hook-form'

import PhoneField from '../../components/PhoneField'
import SectionHeading from '../../components/SectionHeading'
import TextField from '../../components/TextField'
import { useIdentityCheck } from '../../hooks/useIdentityCheck'
import {
  LARGO_DNI,
  MAX_APELLIDO,
  MAX_NOMBRE,
  soloDigitos,
  soloLetras,
} from '../../services/fieldRules'
import DocumentLookup from './DocumentLookup'
import type { WalkInEmergencyFormValues } from './formValues'

interface WalkInClientFieldsProps {
  readonly register: UseFormRegister<WalkInEmergencyFormValues>
  readonly control: Control<WalkInEmergencyFormValues>
  readonly errors: FieldErrors<WalkInEmergencyFormValues>
  readonly setValue: UseFormSetValue<WalkInEmergencyFormValues>
}

/** Los datos del cliente que llega sin cuenta: lo justo para abrir la emergencia. */
export default function WalkInClientFields({
  register,
  control,
  errors,
  setValue,
}: WalkInClientFieldsProps) {
  const dni = useWatch({ control, name: 'document_id' })
  const verificaDni = useIdentityCheck()
  // Lo que llega del DNI se escribe en los campos y se sigue pudiendo corregir.
  const completarNombre = (nombres: string, apellidos: string) => {
    setValue('first_name', nombres, { shouldValidate: true, shouldDirty: true })
    setValue('last_name', apellidos, { shouldValidate: true, shouldDirty: true })
  }

  return (
    <fieldset className="m-0 flex flex-col gap-4 border-0 p-0">
      <legend className="mb-3 p-0">
        <SectionHeading as="h2">Cliente</SectionHeading>
      </legend>
      <div className="grid gap-5 sm:grid-cols-2">
        <TextField
          id="document_id"
          label="DNI"
          placeholder="12345678"
          icon="documento"
          inputMode="numeric"
          maxLength={LARGO_DNI}
          sanitize={soloDigitos}
          field={register('document_id')}
          error={errors.document_id?.message}
        />
        <PhoneField
          id="phone"
          label="Teléfono (si lo tiene a mano)"
          control={control}
          name="phone"
          error={errors.phone?.message}
        />
        {verificaDni ? <DocumentLookup documentId={dni} onFound={completarNombre} /> : null}
        <TextField
          id="first_name"
          label="Nombre"
          placeholder="María"
          icon="perfil"
          maxLength={MAX_NOMBRE}
          sanitize={soloLetras}
          field={register('first_name')}
          error={errors.first_name?.message}
        />
        <TextField
          id="last_name"
          label="Apellido"
          placeholder="Quispe Rojas"
          icon="perfil"
          maxLength={MAX_APELLIDO}
          sanitize={soloLetras}
          field={register('last_name')}
          error={errors.last_name?.message}
        />
      </div>
    </fieldset>
  )
}
