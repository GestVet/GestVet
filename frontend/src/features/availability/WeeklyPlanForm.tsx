import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'

import { applyWeeklyPlan, availabilityQueryKey } from '../../api/availability'
import type { UserResponse } from '../../api/types'
import DialogFormActions from '../../components/DialogFormActions'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import WeeklyPlanFields from './WeeklyPlanFields'
import { horarioVacio, type WeeklyPlanFormValues, weeklyPlanSchema } from './weeklyPlanSchema'

interface WeeklyPlanFormProps {
  readonly veterinarios: readonly UserResponse[]
  readonly onDone: () => void
}

export default function WeeklyPlanForm({ veterinarios, onDone }: WeeklyPlanFormProps) {
  const queryClient = useQueryClient()
  const form = useForm<WeeklyPlanFormValues>({
    resolver: zodResolver(weeklyPlanSchema),
    defaultValues: horarioVacio(),
  })

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
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        form.handleSubmit((valores) => {
          horario.mutate(valores)
        }),
      )}
    >
      <WeeklyPlanFields form={form} veterinarios={veterinarios} />

      {horario.isError ? (
        <FormMessage tone="error">
          {errorMessage(horario.error, 'No se pudo aplicar el horario.')}
        </FormMessage>
      ) : null}
      {horario.isSuccess ? (
        // Queda abierto a propósito: suele cargarse un horario por veterinario.
        <FormMessage tone="ok">
          {`Se asignaron ${String(horario.data.total)} turnos. Puedes aplicar otro horario o cerrar.`}
        </FormMessage>
      ) : null}

      <DialogFormActions>
        <Button type="button" variant="outline" size="lg" className="h-10 px-4" onClick={onDone}>
          {horario.isSuccess ? 'Cerrar' : 'Cancelar'}
        </Button>
        <Button
          type="submit"
          variant="success"
          size="lg"
          className="h-10 px-4"
          disabled={horario.isPending}
        >
          <Icon name="agenda" size={16} />
          <span>{horario.isPending ? 'Aplicando…' : 'Aplicar horario'}</span>
        </Button>
      </DialogFormActions>
    </form>
  )
}
