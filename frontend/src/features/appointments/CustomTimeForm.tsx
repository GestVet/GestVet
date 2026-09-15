import { type KeyboardEvent, useId, useState } from 'react'

import type { GridSlotResponse, ScheduleWindowResponse } from '../../api/types'
import FieldError from '../../components/FieldError'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { formatearHora, formatearHora24, instanteEnClinica } from '../../services/clinicTime'

const MS_POR_MINUTO = 60_000

export interface CustomTimeFormProps {
  readonly veterinarianId: number
  readonly veterinario: string
  /** AAAA-MM-DD en la fecha de la clínica. */
  readonly dia: string
  readonly windows: readonly ScheduleWindowResponse[]
  /** La grilla del día: sirve para ver si la hora escrita cae entre horas ocupadas. */
  readonly slots: readonly GridSlotResponse[]
  readonly durationMinutes: number
  readonly onSelect: (veterinarianId: number, time: string) => void
  readonly onCancel: () => void
}

/**
 * Si la hora escrita cae entre dos cuartos de hora ocupados, choca con una cita.
 *
 * Es una aproximación: en el borde de una cita puede dejar pasar una hora que
 * igual choca, y esa la rechaza el servidor al reservar.
 */
function caeEntreHorasOcupadas(inicio: number, slots: readonly GridSlotResponse[]): boolean {
  const antes = [...slots].reverse().find((slot) => new Date(slot.time).getTime() <= inicio)
  const despues = slots.find((slot) => new Date(slot.time).getTime() >= inicio)
  return antes?.status === 'taken' && despues?.status === 'taken'
}

/** Por qué no sirve una hora escrita a mano, o null si cabe en un turno. */
function problemaDeLaHora(
  instante: string,
  windows: readonly ScheduleWindowResponse[],
  slots: readonly GridSlotResponse[],
  durationMinutes: number,
): string | null {
  const inicio = new Date(instante).getTime()
  if (inicio < Date.now()) {
    return 'Esa hora ya pasó.'
  }
  const turno = windows.find(
    (w) => inicio >= new Date(w.starts_at).getTime() && inicio < new Date(w.ends_at).getTime(),
  )
  if (turno === undefined) {
    return 'Esa hora está fuera del horario del veterinario.'
  }
  if (inicio + durationMinutes * MS_POR_MINUTO > new Date(turno.ends_at).getTime()) {
    return `La cita dura ${String(durationMinutes)} min: empezando a esa hora no termina antes de las ${formatearHora(turno.ends_at)}, cuando acaba el turno.`
  }
  if (caeEntreHorasOcupadas(inicio, slots)) {
    return 'Esa hora se cruza con otra cita del veterinario.'
  }
  return null
}

function ultimoInicioPosible(windows: readonly ScheduleWindowResponse[], durationMinutes: number) {
  const fin = Math.max(...windows.map((w) => new Date(w.ends_at).getTime()))
  return formatearHora24(new Date(fin - durationMinutes * MS_POR_MINUTO).toISOString())
}

/** El campo de hora exacta, validado contra los turnos del día y la duración de la cita. */
export default function CustomTimeForm({
  veterinarianId,
  veterinario,
  dia,
  windows,
  slots,
  durationMinutes,
  onSelect,
  onCancel,
}: CustomTimeFormProps) {
  const [hora, setHora] = useState('')
  const [error, setError] = useState<string | undefined>(undefined)
  const id = useId()
  const turnos = windows
    .map((w) => `${formatearHora(w.starts_at)} a ${formatearHora(w.ends_at)}`)
    .join(' y ')

  function confirmar() {
    const instante = instanteEnClinica(dia, hora)
    const problema = problemaDeLaHora(instante, windows, slots, durationMinutes)
    setError(problema ?? undefined)
    if (problema === null) {
      onSelect(veterinarianId, instante)
    }
  }

  function alPresionarTecla(evento: KeyboardEvent<HTMLInputElement>) {
    // Enter dentro del formulario de reserva lo enviaría entero.
    if (evento.key === 'Enter') {
      evento.preventDefault()
      if (hora !== '') {
        confirmar()
      }
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-lg bg-muted/50 p-3">
      <label htmlFor={id} className="text-sm font-medium">
        Hora personalizada con {veterinario}
      </label>
      <p id={`${id}-ayuda`} className="m-0 text-xs text-muted-foreground">
        La cita dura {durationMinutes} min y tiene que terminar antes de que acabe el turno. Atiende de{' '}
        {turnos}
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <Input
          id={id}
          type="time"
          step={60}
          min={formatearHora24(windows[0].starts_at)}
          max={ultimoInicioPosible(windows, durationMinutes)}
          value={hora}
          aria-describedby={error === undefined ? `${id}-ayuda` : `${id}-ayuda ${id}-error`}
          aria-invalid={error !== undefined}
          className="h-9 w-32 bg-background tabular-nums"
          onChange={(evento) => {
            setHora(evento.target.value)
            setError(undefined)
          }}
          onKeyDown={alPresionarTecla}
        />
        <Button type="button" size="sm" className="h-9" disabled={hora === ''} onClick={confirmar}>
          Usar esta hora
        </Button>
        <Button type="button" variant="ghost" size="sm" className="h-9" onClick={onCancel}>
          Cancelar
        </Button>
      </div>
      <FieldError id={`${id}-error`} message={error} />
    </div>
  )
}
