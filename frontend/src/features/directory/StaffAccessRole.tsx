import { useMutation, useQueryClient } from '@tanstack/react-query'

import { accessQueryKey, assignAccessRole } from '../../api/access'
import type { AccessRoleResponse, UserResponse } from '../../api/types'
import FieldIcon from '../../components/FieldIcon'
import FormMessage from '../../components/FormMessage'
import { NativeSelect, NativeSelectOption } from '../../components/ui/native-select'
import { errorMessage } from '../../services/api'
import { useSession } from '../../store/session'

interface StaffAccessRoleProps {
  readonly account: UserResponse
  readonly roles: readonly AccessRoleResponse[]
  /** Rol asignado a mano. Sin él, la cuenta usa el rol por defecto de su tipo. */
  readonly assignedRoleId: number | undefined
}

/**
 * El rol de una cuenta del personal, elegible entre los de su tipo.
 *
 * La cuenta propia no se puede cambiar: el servidor lo rechaza para que nadie
 * se quite a sí mismo el acceso a esta pantalla.
 */
export default function StaffAccessRole({ account, roles, assignedRoleId }: StaffAccessRoleProps) {
  const queryClient = useQueryClient()
  const esPropia = useSession((state) => state.user?.id === account.id)
  const opciones = roles.filter((rol) => rol.account_kind === account.role)
  const actual = assignedRoleId ?? opciones.find((rol) => rol.is_system)?.id

  const asignacion = useMutation({
    mutationFn: (roleId: number) => assignAccessRole(account.id, roleId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: accessQueryKey })
    },
  })
  // Mientras se guarda se muestra lo elegido, no lo que había.
  const valor = asignacion.isPending ? asignacion.variables : actual

  return (
    <div className="flex min-w-44 flex-col gap-1 whitespace-normal">
      <FieldIcon icon="permisos">
      <NativeSelect
        aria-label={`Rol de ${account.first_name} ${account.last_name}`}
        value={valor === undefined ? '' : String(valor)}
        disabled={esPropia || asignacion.isPending}
        title={esPropia ? 'No puedes cambiar tu propio rol.' : undefined}
        onChange={(evento) => {
          asignacion.mutate(Number(evento.target.value))
        }}
      >
        {opciones.map((rol) => (
          <NativeSelectOption key={rol.id} value={String(rol.id)}>
            {rol.name}
          </NativeSelectOption>
        ))}
      </NativeSelect>
      </FieldIcon>
      {asignacion.isError ? (
        <FormMessage tone="error">
          {errorMessage(asignacion.error, 'No se pudo cambiar el rol.')}
        </FormMessage>
      ) : null}
    </div>
  )
}
