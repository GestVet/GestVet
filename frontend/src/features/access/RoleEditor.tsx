import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useController, useForm, useWatch } from 'react-hook-form'

import { accessQueryKey, createAccessRole, updateAccessRole } from '../../api/access'
import type { AccessRoleResponse, PermissionCatalogResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import PermissionChecklist from './PermissionChecklist'
import RoleFields from './RoleFields'
import { permissionsForKind, roleFormValues, type RoleFormValues, roleSchema } from './roleSchema'

interface RoleEditorProps {
  readonly catalog: PermissionCatalogResponse
  /** El rol a editar. Sin él, el formulario crea uno nuevo. */
  readonly role: AccessRoleResponse | null
  readonly onDone: () => void
}

function guardar(
  role: AccessRoleResponse | null,
  valores: RoleFormValues,
  catalog: PermissionCatalogResponse,
): Promise<AccessRoleResponse> {
  // Cambiar el tipo de cuenta deja marcadas casillas que el nuevo tipo no
  // admite; se descartan acá en vez de dejar que el servidor rechace el rol.
  const permitidos = permissionsForKind(catalog, valores.account_kind)
  const cuerpo = {
    name: valores.name,
    description: valores.description,
    permissions: valores.permissions.filter((code) => permitidos.has(code)),
  }
  if (role === null) {
    return createAccessRole({ ...cuerpo, account_kind: valores.account_kind })
  }
  return updateAccessRole(role.id, cuerpo)
}

export default function RoleEditor({ catalog, role, onDone }: RoleEditorProps) {
  const queryClient = useQueryClient()
  const { register, handleSubmit, control, formState } = useForm<RoleFormValues>({
    resolver: zodResolver(roleSchema),
    defaultValues: roleFormValues(role),
  })
  const permisos = useController({ control, name: 'permissions' })
  const tipo = useWatch({ control, name: 'account_kind' })

  const guardado = useMutation({
    mutationFn: (valores: RoleFormValues) => guardar(role, valores, catalog),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: accessQueryKey })
      onDone()
    },
  })
  const etiqueta = role === null ? 'Crear rol' : 'Guardar cambios'

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          guardado.mutate(valores)
        }),
      )}
    >
      <RoleFields
        register={register}
        errors={formState.errors}
        isNew={role === null}
        isSystem={role?.is_system ?? false}
      />
      <PermissionChecklist
        catalog={catalog}
        kind={tipo}
        value={permisos.field.value}
        onChange={permisos.field.onChange}
      />

      {guardado.isError ? (
        <FormMessage tone="error">
          {errorMessage(guardado.error, 'No se pudo guardar el rol.')}
        </FormMessage>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" variant="success" size="lg" className="h-10 px-4" disabled={guardado.isPending}>
          <Icon name="confirmar" size={16} />
          <span>{guardado.isPending ? 'Guardando…' : etiqueta}</span>
        </Button>
        <Button type="button" variant="outline" size="lg" className="h-10 px-4" onClick={onDone}>
          Cancelar
        </Button>
      </div>
    </form>
  )
}
