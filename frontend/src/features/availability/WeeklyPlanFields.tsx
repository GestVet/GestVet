import { type UseFormReturn, useWatch } from 'react-hook-form'

import type { UserResponse } from '../../api/types'
import SelectField from '../../components/SelectField'
import TextField from '../../components/TextField'
import { NativeSelectOption } from '../../components/ui/native-select'
import ShiftKindSelect from './ShiftKindSelect'
import ShiftPresets, { type HorarioRapido } from './ShiftPresets'
import { limitesDeFecha } from './shiftSchema'
import VeterinarianSelect from './VeterinarianSelect'
import WeekdayPicker from './WeekdayPicker'
import { MAX_SEMANAS, type WeeklyPlanFormValues } from './weeklyPlanSchema'

const SEMANAS = Array.from({ length: MAX_SEMANAS }, (_, indice) => indice + 1)

interface WeeklyPlanFieldsProps {
  readonly form: UseFormReturn<WeeklyPlanFormValues>
  readonly veterinarios: readonly UserResponse[]
}

/** Quién, desde cuándo y cuántas semanas; qué días; y de qué hora a qué hora. */
export default function WeeklyPlanFields({ form, veterinarios }: WeeklyPlanFieldsProps) {
  const { register, setValue, control, formState } = form
  const [desde, hasta, kind] = useWatch({ control, name: ['desde', 'hasta', 'kind'] })
  const errores = formState.errors
  const limites = limitesDeFecha()
  const elegir = (horario: HorarioRapido) => {
    const opciones = { shouldDirty: true, shouldValidate: formState.isSubmitted }
    setValue('desde', horario.desde, opciones)
    setValue('hasta', horario.hasta, opciones)
    setValue('kind', horario.kind, opciones)
  }

  return (
    <div className="grid gap-5 sm:grid-cols-2">
      <VeterinarianSelect
        id="plan-veterinario"
        veterinarios={veterinarios}
        field={register('veterinarian_id')}
        error={errores.veterinarian_id?.message}
      />
      <TextField
        id="plan-desde-dia"
        label="Desde el"
        type="date"
        min={limites.min}
        max={limites.max}
        field={register('first_day')}
        error={errores.first_day?.message}
      />
      <SelectField
        id="plan-semanas"
        label="Durante"
        icon="repetir"
        field={register('weeks')}
        error={errores.weeks?.message}
      >
        {SEMANAS.map((semanas) => (
          <NativeSelectOption key={semanas} value={String(semanas)}>
            {semanas === 1 ? '1 semana' : `${String(semanas)} semanas`}
          </NativeSelectOption>
        ))}
      </SelectField>
      <ShiftKindSelect id="plan-tipo" field={register('kind')} />
      <WeekdayPicker control={control} />
      <ShiftPresets id="plan-rapido" desde={desde} hasta={hasta} kind={kind} onElegir={elegir} />
      <TextField
        id="plan-desde"
        label="Desde"
        type="time"
        step="900"
        field={register('desde')}
        error={errores.desde?.message}
      />
      <TextField
        id="plan-hasta"
        label="Hasta"
        type="time"
        step="900"
        field={register('hasta')}
        error={errores.hasta?.message}
      />
    </div>
  )
}
