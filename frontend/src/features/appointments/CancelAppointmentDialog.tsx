import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { appointmentsQueryKey, cancelAppointment } from '../../api/appointments'
import FormMessage from '../../components/FormMessage'
import { MIN_TEXTO, textoObligatorio } from '../../components/formRules'
import Icon from '../../components/Icon'
import TextareaField from '../../components/TextareaField'
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '../../components/ui/alert-dialog'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

// El mismo tope que el servidor.
const MAX_MOTIVO = 300

const esquema = z.object({ motivo: textoObligatorio(MAX_MOTIVO, 'Escribe el motivo') })

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = { motivo: '' }

interface CancelAppointmentDialogProps {
  readonly appointmentId: number
}

/**
 * Cancela una cita con el motivo, que el backend exige.
 *
 * Reemplaza a `window.prompt`: no tomaba el tema, no se leía bien con lector
 * de pantalla y un navegador lo puede silenciar.
 */
export default function CancelAppointmentDialog({ appointmentId }: CancelAppointmentDialogProps) {
  const queryClient = useQueryClient()
  const [abierto, setAbierto] = useState(false)
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })

  const cancelar = useMutation({
    mutationFn: (valores: Formulario) => cancelAppointment(appointmentId, valores.motivo),
    onSuccess: async () => {
      setAbierto(false)
      reset(VACIO)
      await queryClient.invalidateQueries({ queryKey: appointmentsQueryKey })
    },
  })

  return (
    <AlertDialog
      open={abierto}
      onOpenChange={(abrir) => {
        setAbierto(abrir)
        reset(VACIO)
      }}
    >
      <AlertDialogTrigger asChild>
        <Button type="button" size="sm" variant="destructive">
          <Icon name="cancelar" size={14} />
          <span>Cancelar</span>
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <form
          noValidate
          className="grid gap-4"
          onSubmit={onSubmit(handleSubmit((valores) => { cancelar.mutate(valores) }))}
        >
          <AlertDialogHeader>
            <AlertDialogTitle>Cancelar la cita</AlertDialogTitle>
            <AlertDialogDescription>
              El motivo queda registrado y lo ve la otra parte de la cita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <TextareaField
            id={`motivo-cancelacion-${String(appointmentId)}`}
            label="Motivo"
            icon="mensaje"
            rows={2}
            maxLength={MAX_MOTIVO}
            placeholder="No podré llegar a esa hora"
            hint={`Entre ${String(MIN_TEXTO)} y ${String(MAX_MOTIVO)} caracteres.`}
            field={register('motivo')}
            error={formState.errors.motivo?.message}
          />
          {cancelar.isError ? (
            <FormMessage tone="error">
              {errorMessage(cancelar.error, 'No se pudo cancelar la cita.')}
            </FormMessage>
          ) : null}
          <AlertDialogFooter>
            <AlertDialogCancel>Volver</AlertDialogCancel>
            <Button type="submit" variant="danger" disabled={cancelar.isPending}>
              {cancelar.isPending ? 'Cancelando…' : 'Cancelar cita'}
            </Button>
          </AlertDialogFooter>
        </form>
      </AlertDialogContent>
    </AlertDialog>
  )
}
