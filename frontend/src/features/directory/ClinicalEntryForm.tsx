import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { addClinicalEntry, clinicalEntriesQueryKey } from '../../api/medicalRecords'
import FieldError from '../../components/FieldError'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SelectField from '../../components/SelectField'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const TIPOS = [
  { value: 'consultation', label: 'Consulta' },
  { value: 'vaccine', label: 'Vacuna' },
  { value: 'surgery', label: 'Cirugía' },
  { value: 'follow_up', label: 'Control' },
  { value: 'other', label: 'Otro' },
] as const

const esquema = z.object({
  kind: z.enum(['consultation', 'vaccine', 'surgery', 'follow_up', 'other']),
  notes: z.string().min(1, 'Ingresá una nota'),
  diagnosis: z.string().max(300).optional(),
  treatment: z.string().max(300).optional(),
  weight_kg: z.string().optional(),
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

  const alta = useMutation({
    mutationFn: (valores: Formulario) =>
      addClinicalEntry({
        pet_id: petId,
        kind: valores.kind,
        notes: valores.notes,
        diagnosis: valores.diagnosis ?? '',
        treatment: valores.treatment ?? '',
        weight_kg: valores.weight_kg === '' ? null : valores.weight_kg,
      }),
    onSuccess: async () => {
      reset(VACIO)
      await queryClient.invalidateQueries({ queryKey })
    },
  })

  return (
    <form
      className="form"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          alta.mutate(valores)
        }),
      )}
    >
      <SelectField id="kind" label="Tipo" field={register('kind')}>
        {TIPOS.map((tipo) => (
          <option key={tipo.value} value={tipo.value}>
            {tipo.label}
          </option>
        ))}
      </SelectField>

      <div className="field">
        <label htmlFor="notes">Notas</label>
        <textarea id="notes" rows={2} {...register('notes')} />
        <FieldError message={formState.errors.notes?.message} />
      </div>

      <div className="field">
        <label htmlFor="diagnosis">Diagnóstico</label>
        <input id="diagnosis" {...register('diagnosis')} />
      </div>

      <div className="field">
        <label htmlFor="treatment">Tratamiento</label>
        <input id="treatment" {...register('treatment')} />
      </div>

      <div className="field">
        <label htmlFor="weight_kg">Peso (kg)</label>
        <input id="weight_kg" type="number" step="0.1" min="0" {...register('weight_kg')} />
      </div>

      {alta.isError ? (
        <FormMessage tone="error">
          {errorMessage(alta.error, 'No se pudo agregar la entrada.')}
        </FormMessage>
      ) : null}

      <button type="submit" className="btn btn-green" disabled={alta.isPending}>
        <Icon name="agregar" size={16} />
        <span>{alta.isPending ? 'Guardando…' : 'Agregar a la historia clínica'}</span>
      </button>
    </form>
  )
}
