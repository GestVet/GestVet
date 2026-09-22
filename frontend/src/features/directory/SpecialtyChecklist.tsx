import type { SpecialtyListResponse } from '../../api/types'
import { Checkbox } from '../../components/ui/checkbox'
import { Label } from '../../components/ui/label'

interface SpecialtyChecklistProps {
  readonly catalog: SpecialtyListResponse
  readonly value: readonly number[]
  readonly onChange: (specialtyIds: number[]) => void
}

/**
 * Las especialidades del catálogo, agrupadas como las presentó la clínica.
 *
 * El nombre del grupo lo manda el servidor (`category_label`): así una
 * categoría nueva no exige tocar el frontend.
 */
export default function SpecialtyChecklist({ catalog, value, onChange }: SpecialtyChecklistProps) {
  const alternar = (specialtyId: number, marcado: boolean) => {
    onChange(marcado ? [...value, specialtyId] : value.filter((actual) => actual !== specialtyId))
  }

  const categorias = [...new Set(catalog.items.map((item) => item.category))]

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {categorias.map((categoria) => {
        const items = catalog.items.filter((item) => item.category === categoria)
        if (items.length === 0) {
          return null
        }
        return (
          <fieldset key={categoria} className="m-0 flex flex-col gap-3 rounded-lg border p-4">
            <legend className="px-1 text-sm font-semibold">{items[0].category_label}</legend>
            {items.map((item) => {
              const id = `especialidad-${String(item.id)}`
              return (
                <div key={item.id} className="flex items-center gap-2">
                  <Checkbox
                    id={id}
                    checked={value.includes(item.id)}
                    onCheckedChange={(marcado) => {
                      alternar(item.id, marcado === true)
                    }}
                  />
                  <Label htmlFor={id} className="font-normal">
                    {item.name}
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
