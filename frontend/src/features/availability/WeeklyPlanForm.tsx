import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'

import { applyWeeklyPlan, availabilityQueryKey } from '../../api/availability'
import type { UserResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SectionCard from '../../components/SectionCard'
import SelectField from '../../components/SelectField'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { NativeSelectOption } from '../../components/ui/native-select'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import ShiftKindSelect from './ShiftKindSelect'
import { limitesDeFecha } from './shiftSchema'
import VeterinarianSelect from './VeterinarianSelect'
import WeekdayPicker from './WeekdayPicker'
import {
  horarioVacio,
  MAX_SEMANAS,
  type WeeklyPlanFormValues,
  weeklyPlanSchema,
} from './weeklyPlanSchema'

const SEMANAS = Array.from({ length: MAX_SEMANAS }, (_, indice) => indice + 1)

interface WeeklyPlanFormProps {
  readonly veterinarios: readonly UserResponse[]
}

export default function WeeklyPlanForm({ veterinarios }: WeeklyPlanFormProps) {
  const queryClient = useQueryClient()
  const { register, handleSubmit, control, formState } = useForm<WeeklyPlanFormValues>({
    resolver: zodResolver(weeklyPlanSchema),
    defaultValues: horarioVacio(),
  })
  const limites = limitesDeFecha()

  const horario = useMutation({
    mutationFn: (valores: WeeklyPlanFormValues) =>
      applyWeeklyPlan({
        veterinarian_id: Number(valores.veterinarian_id),
        first_day: valores.first_day,
        weeks: Number(valores.weeks),
        shifts: valores.weekdays.map((weekday) => ({
          weekday,
          starts: valores.desde,
          ends: valores.hasta,
          kind: valores.kind,
        })),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: availabilityQueryKey })
    },
  })

  return (
    <SectionCard
      title="Horario semanal"
      description="Repite el mismo horario varias semanas. Si algún día choca con otro turno, no se asigna ninguno."
    >
      <form
        noValidate
        className="flex flex-col gap-5"
        onSubmit={onSubmit(handleSubmit((valores) => { horario.mutate(valores) }))}
      >
        <div className="grid gap-5 sm:grid-cols-2">
          <VeterinarianSelect id="plan-veterinario" veterinarios={veterinarios} field={register('veterinarian_id')} error={formState.errors.veterinarian_id?.message} />
          <TextField id="plan-desde-dia" label="Desde el" type="date" min={limites.min} max={limites.max} field={register('first_day')} error={formState.errors.first_day?.message} />
          <SelectField id="plan-semanas" label="Durante" icon="repetir" field={register('weeks')} error={formState.errors.weeks?.message}>
            {SEMANAS.map((semanas) => (
              <NativeSelectOption key={semanas} value={String(semanas)}>
                {semanas === 1 ? '1 semana' : `${String(semanas)} semanas`}
              </NativeSelectOption>
            ))}
          </SelectField>
          <ShiftKindSelect id="plan-tipo" field={register('kind')} />
          <WeekdayPicker control={control} />
          <TextField id="plan-desde" label="Desde" type="time" step="900" field={register('desde')} error={formState.errors.desde?.message} />
          <TextField id="plan-hasta" label="Hasta" type="time" step="900" field={register('hasta')} error={formState.errors.hasta?.message} />
        </div>

        {horario.isError ? (
          <FormMessage tone="error">{errorMessage(horario.error, 'No se pudo aplicar el horario.')}</FormMessage>
        ) : null}
        {horario.isSuccess ? (
          <p role="status" className="m-0 text-sm font-medium text-success">
            {`Se asignaron ${String(horario.data.total)} turnos.`}
          </p>
        ) : null}

        <Button type="submit" variant="success" size="lg" className="h-10 self-start px-4" disabled={horario.isPending}>
          <Icon name="agenda" size={16} />
          <span>{horario.isPending ? 'Aplicando…' : 'Aplicar horario'}</span>
        </Button>
      </form>
    </SectionCard>
  )
}
