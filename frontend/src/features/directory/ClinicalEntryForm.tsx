import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { addClinicalEntry, clinicalEntriesQueryKey } from '../../api/medicalRecords'
import FormMessage from '../../components/FormMessage'
import {
  decimalParaApi,
  decimalRule,
  textoObligatorio,
  textoOpcional,
} from '../../components/formRules'
import Icon from '../../components/Icon'
import SelectField from '../../components/SelectField'
import TextareaField from '../../components/TextareaField'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { NativeSelectOption } from '../../components/ui/native-select'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const TIPOS = [
  { value: 'consultation', label: 'Consulta' },
  { value: 'vaccine', label: 'Vacuna' },
  { value: 'surgery', label: 'Cirugía' },
  { value: 'follow_up', label: 'Control' },
  { value: 'consent_form', label: 'Carta de consentimiento' },
  { value: 'other', label: 'Otro' },
] as const

const esquema = z.object({
  kind: z.enum(['consultation', 'vaccine', 'surgery', 'follow_up', 'consent_form', 'other']),
  notes: textoObligatorio(2000, 'Escribe una nota'),
  diagnosis: textoOpcional(300),
  treatment: textoOpcional(300),
  weight_kg: decimalRule({ max: 120, decimales: 2, unidad: 'kg' }),
})

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = {
  kind: 'consultation',
  notes: '',
  diagnosis: '',
  treatment: '',
  weight_kg: '',
}

interface ClinicalEntryFormProps {
  readonly petId: number
}

export default function ClinicalEntryForm({ petId }: ClinicalEntryFormProps) {
  const queryClient = useQueryClient()
  const queryKey = clinicalEntriesQueryKey(petId)
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })
  const campo = (nombre: string) => `${nombre}-${String(petId)}`

  const alta = useMutation({
    mutationFn: (valores: Formulario) =>
      addClinicalEntry({
        pet_id: petId,
        kind: valores.kind,
        notes: valores.notes,
        diagnosis: valores.diagnosis,
        treatment: valores.treatment,
        weight_kg: decimalParaApi(valores.weight_kg),
      }),
    onSuccess: async () => {
      reset(VACIO)
      await queryClient.invalidateQueries({ queryKey })
    },
  })

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          alta.mutate(valores)
        }),
      )}
    >
      <div className="grid gap-5 sm:grid-cols-2">
        <SelectField id={campo('kind')} label="Tipo" icon="registroClinico" field={register('kind')}>
          {TIPOS.map((tipo) => (
            <NativeSelectOption key={tipo.value} value={tipo.value}>
              {tipo.label}
            </NativeSelectOption>
          ))}
        </SelectField>
        <TextField
          id={campo('weight_kg')}
          label="Peso (kg)"
          icon="peso"
          type="number"
          inputMode="decimal"
          step="0.1"
          min="0"
          field={register('weight_kg')}
          error={formState.errors.weight_kg?.message}
        />
        <TextField id={campo('diagnosis')} label="Diagnóstico" icon="diagnostico" maxLength={300} field={register('diagnosis')} error={formState.errors.diagnosis?.message} />
        <TextField id={campo('treatment')} label="Tratamiento" icon="tratamiento" maxLength={300} field={register('treatment')} error={formState.errors.treatment?.message} />
      </div>
      <TextareaField
        id={campo('notes')}
        label="Notas"
        icon="nota"
        rows={2}
        field={register('notes')}
        error={formState.errors.notes?.message}
      />

      {alta.isError ? (
        <FormMessage tone="error">
          {errorMessage(alta.error, 'No se pudo agregar la entrada.')}
        </FormMessage>
      ) : null}

      <Button type="submit" variant="success" className="self-start" disabled={alta.isPending}>
        <Icon name="agregar" size={16} />
        <span>{alta.isPending ? 'Guardando…' : 'Agregar a la historia clínica'}</span>
      </Button>
    </form>
  )
}
