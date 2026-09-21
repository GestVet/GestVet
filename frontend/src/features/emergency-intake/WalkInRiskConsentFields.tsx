import { useEffect } from 'react'
import {
  type Control,
  Controller,
  type FieldErrors,
  type UseFormRegister,
  type UseFormSetValue,
  useWatch,
} from 'react-hook-form'

import type { ConsentTemplateResponse } from '../../api/types'
import ConsentCheckboxField from '../../components/ConsentCheckboxField'
import ConsentText from '../../components/ConsentText'
import SectionHeading from '../../components/SectionHeading'
import TextField from '../../components/TextField'
import { MAX_FIRMA } from '../../services/fieldRules'
import type { WalkInEmergencyFormValues } from './formValues'

interface WalkInRiskConsentFieldsProps {
  readonly register: UseFormRegister<WalkInEmergencyFormValues>
  readonly control: Control<WalkInEmergencyFormValues>
  readonly errors: FieldErrors<WalkInEmergencyFormValues>
  readonly setValue: UseFormSetValue<WalkInEmergencyFormValues>
  /** Si el personal ya corrigió el nombre de quien firma: deja de copiarse del cliente. */
  readonly signerEdited: boolean
  readonly template: ConsentTemplateResponse | undefined
  readonly templateError: boolean
}

/**
 * La aceptación del riesgo en el mostrador.
 *
 * El responsable lee el texto en la pantalla (o se lo leen) y el personal
 * marca que lo aceptó en su presencia. Quien firma suele ser el mismo
 * cliente que se está registrando, así que el nombre se copia de ahí hasta
 * que el personal lo cambie: puede ser un familiar el que trae al animal.
 */
export default function WalkInRiskConsentFields({
  register,
  control,
  errors,
  setValue,
  signerEdited,
  template,
  templateError,
}: WalkInRiskConsentFieldsProps) {
  const [nombre, apellido] = useWatch({ control, name: ['first_name', 'last_name'] })

  useEffect(() => {
    if (!signerEdited) {
      setValue('signer_name', `${nombre} ${apellido}`.trim())
    }
  }, [nombre, apellido, signerEdited, setValue])

  return (
    <fieldset className="m-0 flex flex-col gap-4 border-0 p-0">
      <legend className="mb-3 p-0">
        <SectionHeading as="h2">Aceptación del riesgo</SectionHeading>
      </legend>

      <ConsentText id="mostrador-consentimiento" template={template} isError={templateError} />

      <Controller
        control={control}
        name="risk_accepted"
        render={({ field }) => (
          <ConsentCheckboxField
            id="mostrador-acepto"
            label="El responsable leyó y aceptó este consentimiento en mi presencia"
            checked={field.value}
            onCheckedChange={field.onChange}
            onBlur={field.onBlur}
            inputRef={field.ref}
            error={errors.risk_accepted?.message}
          />
        )}
      />

      <TextField
        id="signer_name"
        label="Nombre completo del responsable"
        icon="perfil"
        maxLength={MAX_FIRMA}
        field={register('signer_name')}
        error={errors.signer_name?.message}
      />
    </fieldset>
  )
}
