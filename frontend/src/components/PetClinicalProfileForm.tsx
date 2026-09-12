import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { onSubmit } from '../hooks/formSubmit'
import { usePetClinicalProfileUpdate } from '../hooks/usePetProfile'
import FormMessage from './FormMessage'
import Icon from './Icon'
import SelectField from './SelectField'
import TextareaField from './TextareaField'
import TextField from './TextField'
import { Button } from './ui/button'
import { NativeSelectOption } from './ui/native-select'

const esquema = z.object({
  weight_kg: z.string(),
  height_cm: z.string(),
  is_sterilized: z.enum(['', 'true', 'false']),
  allergies: z.string().max(300),
})

type Formulario = z.infer<typeof esquema>

interface PetClinicalProfileFormProps {
  readonly petId: number
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
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          guardar.mutate({
            weight_kg: valores.weight_kg === '' ? null : valores.weight_kg,
            height_cm: valores.height_cm === '' ? null : valores.height_cm,
            is_sterilized: valores.is_sterilized === '' ? null : valores.is_sterilized === 'true',
            allergies: valores.allergies,
          })
        }),
      )}
    >
      <div className="grid gap-5 sm:grid-cols-3">
        <TextField
          id="weight_kg"
          label="Peso (kg)"
          type="number"
          inputMode="decimal"
          step="0.1"
          min="0"
          field={register('weight_kg')}
          error={errores.weight_kg?.message}
        />
        <TextField
          id="height_cm"
          label="Altura (cm)"
          type="number"
          inputMode="decimal"
          step="0.1"
          min="0"
          field={register('height_cm')}
          error={errores.height_cm?.message}
        />
        <SelectField
          id="is_sterilized"
          label="Esterilizado"
          field={register('is_sterilized')}
          placeholder="No evaluado"
        >
          <NativeSelectOption value="true">Sí</NativeSelectOption>
          <NativeSelectOption value="false">No</NativeSelectOption>
        </SelectField>
      </div>
      <TextareaField
        id="allergies"
        label="Alergias / condiciones crónicas"
        rows={2}
        field={register('allergies')}
        error={errores.allergies?.message}
      />

      {guardar.isError ? <FormMessage tone="error">{guardar.errorMessage}</FormMessage> : null}

      <Button type="submit" className="self-start" disabled={guardar.isPending}>
        <Icon name="confirmar" size={16} />
        <span>{guardar.isPending ? 'Guardando…' : 'Guardar datos clínicos'}</span>
      </Button>
    </form>
  )
}
