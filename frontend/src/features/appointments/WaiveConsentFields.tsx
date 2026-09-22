import type { FieldErrors, UseFormRegister } from 'react-hook-form'

import SelectField from '../../components/SelectField'
import TextareaField from '../../components/TextareaField'
import { NativeSelectOption } from '../../components/ui/native-select'
import { REQUESTABLE_KINDS } from './requestConsentSchema'
import { MAX_JUSTIFICACION, type WaiveConsentInput } from './waiveConsentSchema'

interface WaiveConsentFieldsProps {
  readonly register: UseFormRegister<WaiveConsentInput>
  readonly errors: FieldErrors<WaiveConsentInput>
}

/** Qué consentimiento no se pudo pedir y por qué. */
export default function WaiveConsentFields({ register, errors }: WaiveConsentFieldsProps) {
  return (
    <>
      <SelectField
        id="urgencia-tipo"
        label="Consentimiento que no se pudo pedir"
        icon="consentimiento"
        placeholder="Elige el consentimiento"
        field={register('kind')}
        error={errors.kind?.message}
      >
        {REQUESTABLE_KINDS.map((opcion) => (
          <NativeSelectOption key={opcion.value} value={opcion.value}>
            {opcion.label}
          </NativeSelectOption>
        ))}
      </SelectField>
      <TextareaField
        id="urgencia-justificacion"
        label="Justificación"
        placeholder="Llegó en paro respiratorio; se llamó dos veces al responsable sin respuesta."
        icon="alerta"
        rows={4}
        maxLength={MAX_JUSTIFICACION}
        field={register('justification')}
        error={errors.justification?.message}
      />
    </>
  )
}
