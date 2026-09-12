import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { appointmentsQueryKey, cancelAppointment } from '../../api/appointments'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
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
import { Label } from '../../components/ui/label'
import { Textarea } from '../../components/ui/textarea'
import { errorMessage } from '../../services/api'

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
  const [motivo, setMotivo] = useState('')
  const motivoId = `motivo-cancelacion-${String(appointmentId)}`

  const cancelar = useMutation({
    mutationFn: () => cancelAppointment(appointmentId, motivo),
    onSuccess: async () => {
      setAbierto(false)
      setMotivo('')
      await queryClient.invalidateQueries({ queryKey: appointmentsQueryKey })
    },
  })

  return (
    <AlertDialog open={abierto} onOpenChange={setAbierto}>
      <AlertDialogTrigger asChild>
        <Button type="button" size="sm" variant="destructive">
          <Icon name="cancelar" size={14} />
          <span>Cancelar</span>
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Cancelar la cita</AlertDialogTitle>
          <AlertDialogDescription>
            El motivo queda registrado y lo ve la otra parte de la cita.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div className="flex flex-col gap-2">
          <Label htmlFor={motivoId}>Motivo</Label>
          <Textarea
            id={motivoId}
            rows={2}
            value={motivo}
            onChange={(evento) => {
              setMotivo(evento.target.value)
            }}
          />
        </div>
        {cancelar.isError ? (
          <FormMessage tone="error">
            {errorMessage(cancelar.error, 'No se pudo cancelar la cita.')}
          </FormMessage>
        ) : null}
        <AlertDialogFooter>
          <AlertDialogCancel>Volver</AlertDialogCancel>
          <Button
            type="button"
            variant="danger"
            disabled={cancelar.isPending || motivo.trim() === ''}
            onClick={() => {
              cancelar.mutate()
            }}
          >
            {cancelar.isPending ? 'Cancelando…' : 'Cancelar cita'}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
