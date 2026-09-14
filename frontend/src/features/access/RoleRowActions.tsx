import { useMutation, useQueryClient } from '@tanstack/react-query'

import { accessQueryKey, deleteAccessRole } from '../../api/access'
import type { AccessRoleResponse } from '../../api/types'
import ConfirmDialog from '../../components/ConfirmDialog'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'

interface RoleRowActionsProps {
  readonly role: AccessRoleResponse
  readonly onEdit: (role: AccessRoleResponse) => void
}

export default function RoleRowActions({ role, onEdit }: RoleRowActionsProps) {
  const queryClient = useQueryClient()
  const borrado = useMutation({
    mutationFn: () => deleteAccessRole(role.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: accessQueryKey })
    },
  })
  const enUso = role.assigned_count > 0

  return (
    <div className="flex max-w-xs flex-col items-start gap-2 whitespace-normal">
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => {
            onEdit(role)
          }}
        >
          <Icon name="engranaje" size={14} />
          <span>Editar</span>
        </Button>
        {role.is_system ? null : (
          <ConfirmDialog
            trigger={
              <Button
                type="button"
                size="sm"
                variant="ghost"
                disabled={borrado.isPending || enUso}
                title={enUso ? 'Quítale el rol a sus cuentas antes de borrarlo.' : undefined}
              >
                <Icon name="cancelar" size={14} />
                <span>Borrar</span>
              </Button>
            }
            title={`¿Borrar el rol «${role.name}»?`}
            description="Nadie lo tiene asignado, así que ninguna cuenta pierde permisos."
            confirmLabel="Borrar rol"
            onConfirm={() => {
              borrado.mutate()
            }}
          />
        )}
      </div>
      {borrado.isError ? (
        <FormMessage tone="error">{errorMessage(borrado.error, 'No se pudo borrar el rol.')}</FormMessage>
      ) : null}
    </div>
  )
}
