import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { NativeSelect, NativeSelectOption } from '../../components/ui/native-select'

export type Rango = 'dia' | 'semana' | 'mes' | 'todos'

const RANGOS: readonly Rango[] = ['todos', 'dia', 'semana', 'mes']

function esRango(valor: string): valor is Rango {
  return (RANGOS as readonly string[]).includes(valor)
}

interface AvailabilityRangeFilterProps {
  readonly rango: Rango
  readonly ancla: string
  readonly onRangoChange: (rango: Rango) => void
  readonly onAnclaChange: (ancla: string) => void
}

export default function AvailabilityRangeFilter({
  rango,
  ancla,
  onRangoChange,
  onAnclaChange,
}: AvailabilityRangeFilterProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="flex flex-col gap-2">
        <Label htmlFor="rango">Ver por</Label>
        <NativeSelect
          id="rango"
          className="w-full [&_select]:h-10"
          value={rango}
          onChange={(evento) => {
            if (esRango(evento.target.value)) {
              onRangoChange(evento.target.value)
            }
          }}
        >
          <NativeSelectOption value="todos">Todos</NativeSelectOption>
          <NativeSelectOption value="dia">Día</NativeSelectOption>
          <NativeSelectOption value="semana">Semana</NativeSelectOption>
          <NativeSelectOption value="mes">Mes</NativeSelectOption>
        </NativeSelect>
      </div>
      {rango === 'todos' ? null : (
        <div className="flex flex-col gap-2">
          <Label htmlFor="ancla">Desde</Label>
          <Input
            id="ancla"
            type="date"
            className="h-10"
            value={ancla}
            onChange={(evento) => {
              onAnclaChange(evento.target.value)
            }}
          />
        </div>
      )}
    </div>
  )
}
