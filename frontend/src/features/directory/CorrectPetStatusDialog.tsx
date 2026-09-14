import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { correctPetStatus, petsOfOwnerQueryKey } from '../../api/pets'
import type { PetResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import { MIN_TEXTO, textoObligatorio } from '../../components/formRules'
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
  const nuevoEstado = mascota.is_active ? 'fallecida' : 'activa'
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })

  const corregir = useMutation({
    mutationFn: (valores: Formulario) =>
      correctPetStatus(mascota.id, !mascota.is_active, valores.motivo),
    onSuccess: async () => {
      setAbierto(false)
      reset(VACIO)
      await queryClient.invalidateQueries({ queryKey: petsOfOwnerQueryKey(mascota.owner_id) })
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
        <Button type="button" variant="ghost" size="sm">
          Corregir a {nuevoEstado}
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <form
          noValidate
          className="grid gap-4"
          onSubmit={onSubmit(handleSubmit((valores) => { corregir.mutate(valores) }))}
        >
          <AlertDialogHeader>
            <AlertDialogTitle>
              Corregir a {mascota.name} a {nuevoEstado}
            </AlertDialogTitle>
            <AlertDialogDescription>
              Solo para un error de carga. El motivo queda en la bitácora de movimientos.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <TextareaField
            id={`motivo-correccion-${String(mascota.id)}`}
            label="Motivo"
            icon="mensaje"
            rows={2}
            maxLength={MAX_MOTIVO}
            placeholder="Se registró por error"
            hint={`Entre ${String(MIN_TEXTO)} y ${String(MAX_MOTIVO)} caracteres.`}
            field={register('motivo')}
            error={formState.errors.motivo?.message}
          />
          {corregir.isError ? (
            <FormMessage tone="error">
              {errorMessage(corregir.error, 'No se pudo corregir el estado.')}
            </FormMessage>
          ) : null}
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <Button type="submit" disabled={corregir.isPending}>
              {corregir.isPending ? 'Corrigiendo…' : 'Corregir estado'}
            </Button>
          </AlertDialogFooter>
        </form>
      </AlertDialogContent>
    </AlertDialog>
  )
}
