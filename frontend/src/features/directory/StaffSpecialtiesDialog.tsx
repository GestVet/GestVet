import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import {
  assignVeterinarianSpecialties,
  fetchSpecialties,
  specialtiesQueryKey,
  staffSpecialtiesQueryKey,
} from '../../api/directory'
import type { UserResponse } from '../../api/types'
import DialogFormActions from '../../components/DialogFormActions'
import FormDialog from '../../components/FormDialog'
import FormMessage from '../../components/FormMessage'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'
import SpecialtyChecklist from './SpecialtyChecklist'

interface StaffSpecialtiesDialogProps {
  readonly account: UserResponse
  readonly initial: readonly number[]
  readonly onClose: () => void
}

/**
 * La ventana donde se reasignan las especialidades de un veterinario.
 *
 * Se monta solo mientras está abierta: así arranca cada vez con lo que tiene
 * asignado hoy, sin arrastrar la elección de la vez anterior.
 */
export default function StaffSpecialtiesDialog({
  account,
  initial,
  onClose,
}: StaffSpecialtiesDialogProps) {
  const queryClient = useQueryClient()
  const [elegidas, setElegidas] = useState<number[]>([...initial])
  const catalogo = useQuery({ queryKey: specialtiesQueryKey, queryFn: fetchSpecialties })

  const guardado = useMutation({
    mutationFn: () => assignVeterinarianSpecialties(account.id, { specialty_ids: elegidas }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: staffSpecialtiesQueryKey })
      onClose()
    },
  })

  return (
    <FormDialog
      open
      onOpenChange={(open) => {
        if (!open) {
          onClose()
        }
      }}
      title={`Especialidades de ${account.first_name} ${account.last_name}`}
      description="Al menos una: es con lo que el cliente lo encuentra al reservar."
      size="lg"
    >
      {catalogo.isPending ? (
        <p className="m-0 text-sm text-muted-foreground">Cargando especialidades…</p>
      ) : (
        <SpecialtyChecklist
          catalog={catalogo.data ?? { items: [] }}
          value={elegidas}
          onChange={setElegidas}
        />
      )}
      {guardado.isError ? (
        <FormMessage tone="error">
          {errorMessage(guardado.error, 'No se pudieron guardar las especialidades.')}
        </FormMessage>
      ) : null}
      <DialogFormActions>
        <Button type="button" variant="outline" size="lg" className="h-10 px-4" onClick={onClose}>
          Cancelar
        </Button>
        <Button
          type="button"
          variant="success"
          size="lg"
          className="h-10 px-4"
          disabled={elegidas.length === 0 || guardado.isPending}
          onClick={() => {
            guardado.mutate()
          }}
        >
          {guardado.isPending ? 'Guardando…' : 'Guardar'}
        </Button>
      </DialogFormActions>
    </FormDialog>
  )
}
