import type { PermissionCatalogResponse, PermissionCode, UserRole } from '../../api/types'
import { Checkbox } from '../../components/ui/checkbox'
import { Label } from '../../components/ui/label'
import { permissionsForKind } from './roleSchema'

interface PermissionChecklistProps {
  readonly catalog: PermissionCatalogResponse
  readonly kind: UserRole
  readonly value: readonly PermissionCode[]
  readonly onChange: (permissions: PermissionCode[]) => void
}

/**
 * Los permisos de un rol, agrupados como en el menú.
 *
 * Solo se ofrecen los que el tipo de cuenta puede tener: a un cliente no se le
 * puede dar "atender citas", y mostrar la casilla solo invitaría al error.
 */
export default function PermissionChecklist({
  catalog,
  kind,
  value,
  onChange,
}: PermissionChecklistProps) {
  const permitidos = permissionsForKind(catalog, kind)
  const alternar = (code: PermissionCode, marcado: boolean) => {
    onChange(marcado ? [...value, code] : value.filter((actual) => actual !== code))
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {catalog.groups.map((grupo) => {
        const items = catalog.items.filter(
          (item) => item.group === grupo && permitidos.has(item.code),
        )
        if (items.length === 0) {
          return null
        }
        return (
          <fieldset key={grupo} className="m-0 flex flex-col gap-3 rounded-lg border p-4">
            <legend className="px-1 text-sm font-semibold">{grupo}</legend>
            {items.map((item) => {
              const id = `permiso-${item.code}`
              return (
                <div key={item.code} className="flex items-center gap-2">
                  <Checkbox
                    id={id}
                    checked={value.includes(item.code)}
                    onCheckedChange={(marcado) => {
                      alternar(item.code, marcado === true)
                    }}
                  />
                  <Label htmlFor={id} className="font-normal">
                    {item.label}
                  </Label>
                </div>
              )
            })}
          </fieldset>
        )
      })}
    </div>
  )
}
