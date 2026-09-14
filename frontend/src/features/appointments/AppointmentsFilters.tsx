import type { AppointmentStatus } from '../../api/types'
import { Checkbox } from '../../components/ui/checkbox'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { NativeSelect, NativeSelectOption } from '../../components/ui/native-select'

const ESTADOS: readonly { value: AppointmentStatus; label: string }[] = [
  { value: 'pending', label: 'Pendiente' },
  { value: 'confirmed', label: 'Confirmada' },
  { value: 'completed', label: 'Completada' },
  { value: 'cancelled', label: 'Cancelada' },
  { value: 'no_show', label: 'No asistió' },
]

interface AppointmentsFiltersProps {
  readonly estado: string
  readonly desde: string
  readonly hasta: string
  readonly soloEmergencias: boolean
  readonly mostrarEmergencias: boolean
  readonly onEstadoChange: (valor: string) => void
  readonly onDesdeChange: (valor: string) => void
  readonly onHastaChange: (valor: string) => void
  readonly onSoloEmergenciasChange: (valor: boolean) => void
}

export default function AppointmentsFilters({
  estado,
  desde,
  hasta,
  soloEmergencias,
  mostrarEmergencias,
  onEstadoChange,
  onDesdeChange,
  onHastaChange,
  onSoloEmergenciasChange,
}: AppointmentsFiltersProps) {
  return (
    <div className="grid items-end gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="filtro-estado">Estado</Label>
        <NativeSelect
          id="filtro-estado"
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
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="filtro-desde">Desde</Label>
        <Input
          id="filtro-desde"
          type="date"
          className="h-10"
          max={hasta === '' ? undefined : hasta}
          value={desde}
          onChange={(evento) => {
            onDesdeChange(evento.target.value)
          }}
        />
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="filtro-hasta">Hasta</Label>
        <Input
          id="filtro-hasta"
          type="date"
          className="h-10"
          min={desde === '' ? undefined : desde}
          value={hasta}
          onChange={(evento) => {
            onHastaChange(evento.target.value)
          }}
        />
      </div>
      {mostrarEmergencias ? (
        <div className="flex h-10 items-center gap-2">
          <Checkbox
            id="filtro-emergencias"
            checked={soloEmergencias}
            onCheckedChange={(marcado) => {
              onSoloEmergenciasChange(marcado === true)
            }}
          />
          <Label htmlFor="filtro-emergencias">Solo emergencias</Label>
        </div>
      ) : null}
    </div>
  )
}
