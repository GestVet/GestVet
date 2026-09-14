import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { availabilityQueryKey, createChangeRequest } from '../../api/availability'
import type { SlotResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SelectField from '../../components/SelectField'
import TextareaField from '../../components/TextareaField'
import { Button } from '../../components/ui/button'
import { NativeSelectOption } from '../../components/ui/native-select'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import { formatearDiaDeInstante } from '../../services/clinicTime'
import { ETIQUETA_DE_TURNO, horarioDeTurno } from './shiftKinds'

// Los mismos limites que el servidor.
const MIN_MENSAJE = 5
const MAX_MENSAJE = 500

const esquema = z.object({
  slot_id: z.string(),
  message: z
    .string()
    .trim()
    .min(MIN_MENSAJE, 'Cuenta qué necesitas cambiar')
    .max(MAX_MENSAJE, `Usa hasta ${String(MAX_MENSAJE)} caracteres`),
})

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = { slot_id: '', message: '' }

interface ChangeRequestFormProps {
  /** Los turnos que se ven en pantalla. Solo se ofrecen los que no terminaron. */
  readonly turnos: readonly SlotResponse[]
}

export default function ChangeRequestForm({ turnos }: ChangeRequestFormProps) {
  const queryClient = useQueryClient()
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })
  // El momento se fija al montar: una lista que cambiara en cada render saltaría.
  const [ahora] = useState(() => Date.now())
  const proximos = turnos.filter((turno) => Date.parse(turno.ends_at) > ahora)

  const pedido = useMutation({
    mutationFn: (valores: Formulario) =>
      createChangeRequest({
        message: valores.message,
        slot_id: valores.slot_id === '' ? null : Number(valores.slot_id),
      }),
    onSuccess: async () => {
      reset(VACIO)
      await queryClient.invalidateQueries({ queryKey: availabilityQueryKey })
    },
  })

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          pedido.mutate(valores)
        }),
      )}
    >
      <SelectField
        id="cambio-turno"
        label="Turno"
        icon="turno"
        placeholder="Ninguno en particular"
        hint="Solo aparecen los turnos de la semana que estás viendo."
        field={register('slot_id')}
      >
        {proximos.map((turno) => (
          <NativeSelectOption key={turno.id} value={String(turno.id)}>
            {`${formatearDiaDeInstante(turno.starts_at)}, ${horarioDeTurno(turno)} (${ETIQUETA_DE_TURNO[turno.kind]})`}
          </NativeSelectOption>
        ))}
      </SelectField>
      <TextareaField
        id="cambio-mensaje"
        label="Qué necesitas"
        icon="mensaje"
        placeholder="Tengo control médico el martes por la mañana"
        field={register('message')}
        error={formState.errors.message?.message}
      />

      {pedido.isError ? (
        <FormMessage tone="error">{errorMessage(pedido.error, 'No se pudo enviar el pedido.')}</FormMessage>
      ) : null}

      <Button
        type="submit"
        size="lg"
        className="h-10 self-start px-4"
        disabled={pedido.isPending}
      >
        <Icon name="correo" size={16} />
        <span>{pedido.isPending ? 'Enviando…' : 'Enviar pedido'}</span>
      </Button>
    </form>
  )
}
