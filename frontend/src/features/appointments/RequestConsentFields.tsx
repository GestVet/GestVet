import { useQuery } from '@tanstack/react-query'
import type { FieldErrors, UseFormRegister } from 'react-hook-form'

import { currentTemplateQueryKey, fetchCurrentTemplate } from '../../api/consents'
import ConsentText from '../../components/ConsentText'
import SelectField from '../../components/SelectField'
import TextareaField from '../../components/TextareaField'
import TextField from '../../components/TextField'
import { NativeSelectOption } from '../../components/ui/native-select'
import {
  kindInfo,
  REQUESTABLE_KINDS,
  type RequestableKind,
  type RequestConsentInput,
} from './requestConsentSchema'

interface RequestConsentFieldsProps {
  readonly register: UseFormRegister<RequestConsentInput>
  readonly errors: FieldErrors<RequestConsentInput>
  readonly kind: string
}

/** El tipo, el detalle que completa el veterinario y el texto que va a leer el dueño. */
export default function RequestConsentFields({ register, errors, kind }: RequestConsentFieldsProps) {
  const info = kindInfo(kind)
  const plantilla = useQuery({
    queryKey: currentTemplateQueryKey(kind as RequestableKind),
    queryFn: () => fetchCurrentTemplate(kind as RequestableKind),
    enabled: info !== undefined,
    // Un texto publicado no cambia: una corrección es otra versión.
    staleTime: Infinity,
  })

  return (
    <>
      <SelectField
        id="consentimiento-tipo"
        label="Consentimiento"
        icon="consentimiento"
        placeholder="Elige qué consentimiento pedir"
        field={register('kind')}
        error={errors.kind?.message}
      >
        {REQUESTABLE_KINDS.map((opcion) => (
          <NativeSelectOption key={opcion.value} value={opcion.value}>
            {opcion.label}
          </NativeSelectOption>
        ))}
      </SelectField>

      {info === undefined ? null : (
        <>
          <TextField
            id="consentimiento-procedimiento"
            label={info.procedureLabel}
            icon="tratamiento"
            maxLength={200}
            field={register('procedure')}
            error={errors.procedure?.message}
          />
          <TextareaField
            id="consentimiento-pronostico"
            label="Pronóstico (opcional)"
            icon="diagnostico"
            rows={2}
            maxLength={500}
            field={register('prognosis')}
            error={errors.prognosis?.message}
          />
          <TextField
            id="consentimiento-costo"
            label="Costo estimado en soles (opcional)"
            icon="pago"
            inputMode="decimal"
            placeholder="450.00"
            field={register('estimated_cost')}
            error={errors.estimated_cost?.message}
          />
          <TextareaField
            id="consentimiento-notas"
            label="Observaciones (opcional)"
            icon="nota"
            rows={2}
            maxLength={1000}
            field={register('notes')}
            error={errors.notes?.message}
          />
          <ConsentText
            id="consentimiento-vista-previa"
            template={plantilla.data}
            isError={plantilla.isError}
          />
          <p className="m-0 text-xs text-muted-foreground">
            Debajo del texto se agrega el detalle que completaste. El responsable firma exactamente
            eso.
          </p>
        </>
      )}
    </>
  )
}
