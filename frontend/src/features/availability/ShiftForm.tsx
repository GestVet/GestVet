import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'

import { assignShift, availabilityQueryKey } from '../../api/availability'
import type { UserResponse } from '../../api/types'
import DialogFormActions from '../../components/DialogFormActions'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import ShiftFields from './ShiftFields'
import {
  finDelTurno,
  inicioDelTurno,
  type ShiftFormValues,
  shiftSchema,
  turnoVacio,
} from './shiftSchema'

/** Lo que ya se sabe al abrir: desde una celda del cuadro, el veterinario y el día. */
export interface TurnoInicial {
  readonly veterinarioId?: number
  readonly dia?: string
}

interface ShiftFormProps {
  readonly veterinarios: readonly UserResponse[]
  readonly inicial?: TurnoInicial
  /** Se llama al asignarlo o al cancelar: cierra la ventana. */
  readonly onDone: () => void
}

function valoresIniciales(inicial: TurnoInicial | undefined): ShiftFormValues {
  const vacio = turnoVacio()
  return {
    ...vacio,
    veterinarian_id: inicial?.veterinarioId === undefined ? '' : String(inicial.veterinarioId),
    dia: inicial?.dia ?? vacio.dia,
  }
}

export default function ShiftForm({ veterinarios, inicial, onDone }: ShiftFormProps) {
  const queryClient = useQueryClient()
  const form = useForm<ShiftFormValues>({
    resolver: zodResolver(shiftSchema),
    defaultValues: valoresIniciales(inicial),
  })

  const asignacion = useMutation({
    mutationFn: (valores: ShiftFormValues) =>
      assignShift({
        veterinarian_id: Number(valores.veterinarian_id),
        starts_at: inicioDelTurno(valores),
        ends_at: finDelTurno(valores),
        kind: valores.kind,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: availabilityQueryKey })
      onDone()
    },
  })

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        form.handleSubmit((valores) => {
          asignacion.mutate(valores)
        }),
      )}
    >
      <ShiftFields form={form} veterinarios={veterinarios} />

      {asignacion.isError ? (
        <FormMessage tone="error">
          {errorMessage(asignacion.error, 'No se pudo asignar el turno.')}
        </FormMessage>
      ) : null}

      <DialogFormActions>
        <Button type="button" variant="outline" size="lg" className="h-10 px-4" onClick={onDone}>
          Cancelar
        </Button>
        <Button
          type="submit"
          variant="success"
          size="lg"
          className="h-10 px-4"
          disabled={asignacion.isPending}
        >
          <Icon name="agregar" size={16} />
          <span>{asignacion.isPending ? 'Asignando…' : 'Asignar turno'}</span>
        </Button>
      </DialogFormActions>
    </form>
  )
}
