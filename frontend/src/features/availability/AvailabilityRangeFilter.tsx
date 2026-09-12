export type Rango = 'dia' | 'semana' | 'mes' | 'todos'

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
    <div className="form" style={{ gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
      <div className="field">
        <label htmlFor="rango">Ver por</label>
        <select
          id="rango"
          value={rango}
          onChange={(evento) => {
            onRangoChange(evento.target.value as Rango)
          }}
        >
          <option value="todos">Todos</option>
          <option value="dia">Día</option>
          <option value="semana">Semana</option>
          <option value="mes">Mes</option>
        </select>
      </div>
      {rango === 'todos' ? null : (
        <div className="field">
          <label htmlFor="ancla">Desde</label>
          <input
            id="ancla"
            type="date"
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
