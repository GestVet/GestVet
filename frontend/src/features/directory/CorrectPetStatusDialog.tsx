import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { correctPetStatus, petsOfOwnerQueryKey } from '../../api/pets'
import type { PetResponse } from '../../api/types'
import FieldIcon from '../../components/FieldIcon'
import FormMessage from '../../components/FormMessage'
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

interface CorrectPetStatusDialogProps {
  readonly mascota: PetResponse
}

/**
 * Corrige el estado de una mascota, con el motivo que queda en la bitácora.
 *
 * Distinta de la baja que hace el dueño: acá se puede volver de "fallecida" a
 * "activa", porque es para deshacer un error de carga, no para revivir una
 * mascota. Reemplaza a `window.prompt`, que no se podía leer bien con lector
 * de pantalla y no tomaba el tema.
 */
export default function CorrectPetStatusDialog({ mascota }: CorrectPetStatusDialogProps) {
  const queryClient = useQueryClient()
  const [abierto, setAbierto] = useState(false)
  const [motivo, setMotivo] = useState('')
  const nuevoEstado = mascota.is_active ? 'fallecida' : 'activa'
  const motivoId = `motivo-correccion-${String(mascota.id)}`

  const corregir = useMutation({
    mutationFn: () => correctPetStatus(mascota.id, !mascota.is_active, motivo),
    onSuccess: async () => {
      setAbierto(false)
      setMotivo('')
      await queryClient.invalidateQueries({ queryKey: petsOfOwnerQueryKey(mascota.owner_id) })
    },
  })

  return (
    <AlertDialog open={abierto} onOpenChange={setAbierto}>
      <AlertDialogTrigger asChild>
        <Button type="button" variant="ghost" size="sm">
          Corregir a {nuevoEstado}
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            Corregir a {mascota.name} a {nuevoEstado}
          </AlertDialogTitle>
          <AlertDialogDescription>
            Solo para un error de carga. El motivo queda en la bitácora de movimientos.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div className="flex flex-col gap-2">
          <Label htmlFor={motivoId}>Motivo</Label>
          <FieldIcon icon="mensaje" multiline>
          <Textarea
            id={motivoId}
            rows={2}
            value={motivo}
            onChange={(evento) => {
              setMotivo(evento.target.value)
            }}
          />
          </FieldIcon>
        </div>
        {corregir.isError ? (
          <FormMessage tone="error">
            {errorMessage(corregir.error, 'No se pudo corregir el estado.')}
          </FormMessage>
        ) : null}
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <Button
            type="button"
            disabled={corregir.isPending || motivo.trim() === ''}
            onClick={() => {
              corregir.mutate()
            }}
          >
            {corregir.isPending ? 'Corrigiendo…' : 'Corregir estado'}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
