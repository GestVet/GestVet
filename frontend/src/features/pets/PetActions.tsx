import { useMutation, useQueryClient } from '@tanstack/react-query'

import { changePetStatus, myPetsQueryKey } from '../../api/pets'
import type { PetResponse } from '../../api/types'
import ConfirmDialog from '../../components/ConfirmDialog'
import FormMessage from '../../components/FormMessage'
import RowExpandButton from '../../components/RowExpandButton'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'

interface PetActionsProps {
  readonly mascota: PetResponse
  readonly isExpanded: boolean
  readonly onToggle: () => void
}

/** Ver el detalle de una mascota y registrar su fallecimiento. */
export default function PetActions({ mascota, isExpanded, onToggle }: PetActionsProps) {
  const queryClient = useQueryClient()
  const darDeBaja = useMutation({
    mutationFn: () => changePetStatus(mascota.id, false),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: myPetsQueryKey })
    },
  })

  return (
    <div className="flex max-w-72 flex-col items-start gap-2 whitespace-normal">
      <div className="flex flex-wrap gap-2">
        <RowExpandButton
          isExpanded={isExpanded}
          onToggle={onToggle}
          collapsedLabel="Ver más detalles"
          expandedLabel="Ocultar detalles"
        />
        {mascota.is_active ? (
          <ConfirmDialog
            title={`¿${mascota.name} falleció?`}
            description="Esta acción no se puede deshacer; solo el personal de la clínica puede corregirla si fue un error."
            confirmLabel="Registrar fallecimiento"
            onConfirm={() => {
              darDeBaja.mutate()
            }}
            trigger={
              <Button type="button" variant="ghost" size="sm" disabled={darDeBaja.isPending}>
                Registrar fallecimiento
              </Button>
            }
          />
        ) : null}
      </div>
      {mascota.is_active ? null : (
        <p className="m-0 text-xs text-muted-foreground">
          Si fue un error, pedile al personal de la clínica que lo corrija.
        </p>
      )}
      {darDeBaja.isError ? (
        <FormMessage tone="error">
          {errorMessage(darDeBaja.error, 'No se pudo actualizar el estado.')}
        </FormMessage>
      ) : null}
    </div>
  )
}
