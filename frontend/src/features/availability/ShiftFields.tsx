import { type UseFormReturn, useWatch } from 'react-hook-form'

import type { UserResponse } from '../../api/types'
import TextField from '../../components/TextField'
import ShiftKindSelect from './ShiftKindSelect'
import ShiftPresets, { type HorarioRapido } from './ShiftPresets'
import { limitesDeFecha, type ShiftFormValues } from './shiftSchema'
import VeterinarianSelect from './VeterinarianSelect'

interface ShiftFieldsProps {
  readonly form: UseFormReturn<ShiftFormValues>
  readonly veterinarios: readonly UserResponse[]
}

/** Quién, qué día y de qué hora a qué hora: primero lo rápido, después el ajuste fino. */
export default function ShiftFields({ form, veterinarios }: ShiftFieldsProps) {
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
        id="turno-veterinario"
        veterinarios={veterinarios}
        field={register('veterinarian_id')}
        error={errores.veterinarian_id?.message}
      />
      <TextField
        id="turno-dia"
        label="Día"
        type="date"
        min={limites.min}
        max={limites.max}
        field={register('dia')}
        error={errores.dia?.message}
      />
      <ShiftPresets id="turno-rapido" desde={desde} hasta={hasta} kind={kind} onElegir={elegir} />
      <TextField
        id="turno-desde"
        label="Desde"
        type="time"
        step="900"
        field={register('desde')}
        error={errores.desde?.message}
      />
      <TextField
        id="turno-hasta"
        label="Hasta"
        type="time"
        step="900"
        hint="En una guardia, una hora menor que el inicio es del día siguiente."
        field={register('hasta')}
        error={errores.hasta?.message}
      />
      <div className="sm:col-span-2">
        <ShiftKindSelect id="turno-tipo" field={register('kind')} />
      </div>
    </div>
  )
}
