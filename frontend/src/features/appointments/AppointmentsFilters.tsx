import type { AppointmentStatus } from '../../api/types'

const ESTADOS: readonly { value: AppointmentStatus; label: string }[] = [
  { value: 'pending', label: 'Pendiente' },
  { value: 'confirmed', label: 'Confirmada' },
  { value: 'completed', label: 'Completada' },
  { value: 'cancelled', label: 'Cancelada' },
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
    <div className="form" style={{ gridTemplateColumns: 'repeat(4, minmax(0, 1fr))' }}>
      <div className="field">
        <label htmlFor="filtro-estado">Estado</label>
        <select
          id="filtro-estado"
          value={estado}
          onChange={(evento) => {
            onEstadoChange(evento.target.value)
          }}
        >
          <option value="">Todos</option>
          {ESTADOS.map((opcion) => (
            <option key={opcion.value} value={opcion.value}>
              {opcion.label}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="filtro-desde">Desde</label>
        <input
          id="filtro-desde"
          type="date"
          value={desde}
          onChange={(evento) => {
            onDesdeChange(evento.target.value)
          }}
        />
      </div>
      <div className="field">
        <label htmlFor="filtro-hasta">Hasta</label>
        <input
          id="filtro-hasta"
          type="date"
          value={hasta}
          onChange={(evento) => {
            onHastaChange(evento.target.value)
          }}
        />
      </div>
      {mostrarEmergencias ? (
        <div className="field">
          <label htmlFor="filtro-emergencias">
            <input
              id="filtro-emergencias"
              type="checkbox"
              checked={soloEmergencias}
              onChange={(evento) => {
                onSoloEmergenciasChange(evento.target.checked)
              }}
            />{' '}
            Solo emergencias
          </label>
        </div>
      ) : null}
    </div>
  )
}
