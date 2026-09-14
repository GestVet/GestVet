import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'

import { assignShift, availabilityQueryKey } from '../../api/availability'
import type { UserResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SectionCard from '../../components/SectionCard'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import { sumarDias } from '../../services/clinicTime'
import ShiftKindSelect from './ShiftKindSelect'
import {
  finDelTurno,
  inicioDelTurno,
  limitesDeFecha,
  type ShiftFormValues,
  shiftSchema,
  turnoVacio,
} from './shiftSchema'
import VeterinarianSelect from './VeterinarianSelect'

interface ShiftFormProps {
  readonly veterinarios: readonly UserResponse[]
}

export default function ShiftForm({ veterinarios }: ShiftFormProps) {
  const queryClient = useQueryClient()
  const { register, handleSubmit, reset, formState } = useForm<ShiftFormValues>({
    resolver: zodResolver(shiftSchema),
    defaultValues: turnoVacio(),
  })
  const limites = limitesDeFecha()

  const asignacion = useMutation({
    mutationFn: (valores: ShiftFormValues) =>
      assignShift({
        veterinarian_id: Number(valores.veterinarian_id),
        starts_at: inicioDelTurno(valores),
        ends_at: finDelTurno(valores),
        kind: valores.kind,
      }),
    onSuccess: async (_, valores) => {
      // Se pasa al día siguiente: así se carga una semana de corrido sin
      // volver a elegir veterinario ni horario.
      reset({ ...valores, dia: sumarDias(valores.dia, 1) })
      await queryClient.invalidateQueries({ queryKey: availabilityQueryKey })
    },
  })

  return (
    <SectionCard title="Asignar un turno" description="Para un día puntual o un reemplazo.">
      <form
        noValidate
        className="flex flex-col gap-5"
        onSubmit={onSubmit(
          handleSubmit((valores) => {
            asignacion.mutate(valores)
          }),
        )}
      >
        <div className="grid gap-5 sm:grid-cols-2">
          <VeterinarianSelect
            id="turno-veterinario"
            veterinarios={veterinarios}
            field={register('veterinarian_id')}
            error={formState.errors.veterinarian_id?.message}
          />
          <TextField
            id="turno-dia"
            label="Día"
            type="date"
            min={limites.min}
            max={limites.max}
            field={register('dia')}
            error={formState.errors.dia?.message}
          />
          <TextField id="turno-desde" label="Desde" type="time" step="900" field={register('desde')} error={formState.errors.desde?.message} />
          <TextField
            id="turno-hasta"
            label="Hasta"
            type="time"
            step="900"
            hint="En una guardia, una hora menor que el inicio es del día siguiente."
            field={register('hasta')}
            error={formState.errors.hasta?.message}
          />
          <ShiftKindSelect id="turno-tipo" field={register('kind')} />
        </div>

        {asignacion.isError ? (
          <FormMessage tone="error">{errorMessage(asignacion.error, 'No se pudo asignar el turno.')}</FormMessage>
        ) : null}

        <Button type="submit" variant="success" size="lg" className="h-10 self-start px-4" disabled={asignacion.isPending}>
          <Icon name="agregar" size={16} />
          <span>{asignacion.isPending ? 'Asignando…' : 'Asignar turno'}</span>
        </Button>
      </form>
    </SectionCard>
  )
}
