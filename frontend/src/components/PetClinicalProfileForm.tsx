import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { onSubmit } from '../hooks/formSubmit'
import { usePetClinicalProfileUpdate } from '../hooks/usePetProfile'
import FormMessage from './FormMessage'
import {
  decimalParaApi,
  decimalRule,
  fechaDeNacimientoRule,
  limitesDeNacimiento,
  textoOpcional,
} from './formRules'
import Icon from './Icon'
import SelectField from './SelectField'
import TextareaField from './TextareaField'
import TextField from './TextField'
import { Button } from './ui/button'
import { NativeSelectOption } from './ui/native-select'

const esquema = z.object({
  // La confirma el veterinario: en un alta exprés de emergencia queda provisoria.
  birth_date: fechaDeNacimientoRule,
  // Los mismos topes que el servidor: 120 kg y 200 cm cubren de un hámster a un gran danés.
  weight_kg: decimalRule({ max: 120, decimales: 2, unidad: 'kg' }),
  height_cm: decimalRule({ max: 200, decimales: 1, unidad: 'cm' }),
  is_sterilized: z.enum(['', 'true', 'false']),
  allergies: textoOpcional(300),
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

function paraApi(valores: Formulario, fechaGuardada: string) {
  return {
    // Solo viaja si cambió: guardar el peso no pisa una fecha que corrigió el
    // dueño desde su ficha.
    birth_date: valores.birth_date === fechaGuardada ? null : valores.birth_date,
    weight_kg: decimalParaApi(valores.weight_kg),
    height_cm: decimalParaApi(valores.height_cm),
    is_sterilized: valores.is_sterilized === '' ? null : valores.is_sterilized === 'true',
    allergies: valores.allergies,
  }
}

/**
 * Datos que confirma el veterinario en consulta: fecha de nacimiento, peso,
 * altura, esterilización y alergias.
 */
export default function PetClinicalProfileForm(props: PetClinicalProfileFormProps) {
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: valoresIniciales(props),
  })
  const guardar = usePetClinicalProfileUpdate(props.petId)
  const errores = formState.errors
  const limites = limitesDeNacimiento()

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          guardar.mutate(paraApi(valores, props.birthDate))
        }),
      )}
    >
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <TextField
          id={`clinica-nacimiento-${String(props.petId)}`}
          label="Fecha de nacimiento"
          type="date"
          min={limites.min}
          max={limites.max}
          field={register('birth_date')}
          error={errores.birth_date?.message}
        />
        <TextField
          id="weight_kg"
          label="Peso (kg)"
          placeholder="12.5"
          icon="peso"
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
          placeholder="45"
          icon="altura"
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
          icon="salud"
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
        placeholder="Alergia a la penicilina, dermatitis"
        icon="alergia"
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
