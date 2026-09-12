import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { onSubmit } from '../hooks/formSubmit'
import { usePetClinicalProfileUpdate } from '../hooks/usePetProfile'
import FieldError from './FieldError'
import FormMessage from './FormMessage'
import Icon from './Icon'
import SelectField from './SelectField'

const esquema = z.object({
  birth_date: z.string().min(1, 'Ingresá la fecha de nacimiento'),
  weight_kg: z.string(),
  height_cm: z.string(),
  is_sterilized: z.enum(['', 'true', 'false']),
  allergies: z.string().max(300),
})

type Formulario = z.infer<typeof esquema>

interface PetClinicalProfileFormProps {
  readonly petId: number
  readonly birthDate: string
  readonly weightKg: string | null
  readonly heightCm: string | null
  readonly isSterilized: boolean | null
  readonly allergies: string
}

function esterilizadoInicial(valor: boolean | null): '' | 'true' | 'false' {
  if (valor === null) return ''
  return valor ? 'true' : 'false'
}

function valoresIniciales(props: PetClinicalProfileFormProps): Formulario {
  return {
    birth_date: props.birthDate,
    weight_kg: props.weightKg ?? '',
    height_cm: props.heightCm ?? '',
    is_sterilized: esterilizadoInicial(props.isSterilized),
    allergies: props.allergies,
  }
}

/** Datos que confirma el veterinario en consulta: peso, altura, esterilización y alergias. */
export default function PetClinicalProfileForm(props: PetClinicalProfileFormProps) {
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: valoresIniciales(props),
  })
  const guardar = usePetClinicalProfileUpdate(props.petId)
  const errores = formState.errors

  return (
    <form
      className="form"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          guardar.mutate({
            birth_date: valores.birth_date,
            weight_kg: valores.weight_kg === '' ? null : valores.weight_kg,
            height_cm: valores.height_cm === '' ? null : valores.height_cm,
            is_sterilized: valores.is_sterilized === '' ? null : valores.is_sterilized === 'true',
            allergies: valores.allergies,
          })
        }),
      )}
    >
      <div className="field">
        <label htmlFor="birth_date">Fecha de nacimiento</label>
        <input id="birth_date" type="date" {...register('birth_date')} />
        <FieldError message={errores.birth_date?.message} />
      </div>
      <div className="field">
        <label htmlFor="weight_kg">Peso (kg)</label>
        <input id="weight_kg" type="number" step="0.1" min="0" {...register('weight_kg')} />
        <FieldError message={errores.weight_kg?.message} />
      </div>
      <div className="field">
        <label htmlFor="height_cm">Altura (cm)</label>
        <input id="height_cm" type="number" step="0.1" min="0" {...register('height_cm')} />
        <FieldError message={errores.height_cm?.message} />
      </div>
      <SelectField
        id="is_sterilized"
        label="Esterilizado"
        field={register('is_sterilized')}
        placeholder="No evaluado"
      >
        <option value="true">Sí</option>
        <option value="false">No</option>
      </SelectField>
      <div className="field">
        <label htmlFor="allergies">Alergias / condiciones crónicas</label>
        <textarea id="allergies" rows={2} {...register('allergies')} />
        <FieldError message={errores.allergies?.message} />
      </div>

      {guardar.isError ? <FormMessage tone="error">{guardar.errorMessage}</FormMessage> : null}

      <button type="submit" className="btn btn-blue" disabled={guardar.isPending}>
        <Icon name="confirmar" size={16} />
        <span>{guardar.isPending ? 'Guardando…' : 'Guardar'}</span>
      </button>
    </form>
  )
}
