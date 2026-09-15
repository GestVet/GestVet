import FieldIcon from '../../components/FieldIcon'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { NativeSelect, NativeSelectOption } from '../../components/ui/native-select'

const ESTADOS: readonly { value: string; label: string }[] = [
  { value: 'pending', label: 'Pendiente' },
  { value: 'confirmed', label: 'Confirmada' },
  { value: 'completed', label: 'Completada' },
  { value: 'cancelled', label: 'Cancelada' },
  { value: 'no_show', label: 'No asistió' },
]

interface ServiceConsumptionFiltersProps {
  readonly estado: string
  readonly desde: string
  readonly hasta: string
  readonly onEstadoChange: (valor: string) => void
  readonly onDesdeChange: (valor: string) => void
  readonly onHastaChange: (valor: string) => void
}

export default function ServiceConsumptionFilters({
  estado,
  desde,
  hasta,
  onEstadoChange,
  onDesdeChange,
  onHastaChange,
}: ServiceConsumptionFiltersProps) {
  return (
    <div className="grid items-end gap-4 sm:grid-cols-3">
      <div className="flex flex-col gap-2">
        <Label htmlFor="servicios-estado">Estado</Label>
        <FieldIcon icon="filtro">
          <NativeSelect
            id="servicios-estado"
            className="w-full [&_select]:h-10"
            value={estado}
            onChange={(evento) => {
              onEstadoChange(evento.target.value)
            }}
          >
            <NativeSelectOption value="">Todos</NativeSelectOption>
            {ESTADOS.map((opcion) => (
              <NativeSelectOption key={opcion.value} value={opcion.value}>
                {opcion.label}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </FieldIcon>
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="servicios-desde">Desde</Label>
        <FieldIcon icon="fecha">
          <Input
            id="servicios-desde"
            type="date"
            className="h-10"
            max={hasta === '' ? undefined : hasta}
            value={desde}
            onChange={(evento) => {
              onDesdeChange(evento.target.value)
            }}
          />
        </FieldIcon>
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="servicios-hasta">Hasta</Label>
        <FieldIcon icon="fecha">
          <Input
            id="servicios-hasta"
            type="date"
            className="h-10"
            min={desde === '' ? undefined : desde}
            value={hasta}
            onChange={(evento) => {
              onHastaChange(evento.target.value)
            }}
          />
        </FieldIcon>
      </div>
    </div>
  )
}
