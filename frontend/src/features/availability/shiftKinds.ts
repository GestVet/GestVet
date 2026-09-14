import type { ShiftKind, SlotResponse } from '../../api/types'
import type { StatusTone } from '../../components/StatusBadge'
import { claveDeInstante, formatearHora24 } from '../../services/clinicTime'

export const ETIQUETA_DE_TURNO: Record<ShiftKind, string> = {
  regular: 'Atención',
  on_call: 'Guardia',
}

export const TONO_DE_TURNO: Record<ShiftKind, StatusTone> = {
  regular: 'confirmed',
  on_call: 'pending',
}

/** "20:00 – 08:00 (día siguiente)" para una guardia que cruza la medianoche. */
export function horarioDeTurno(turno: SlotResponse): string {
  const ultimoMinuto = new Date(Date.parse(turno.ends_at) - 1).toISOString()
  const cruza = claveDeInstante(turno.starts_at) !== claveDeInstante(ultimoMinuto)
  const rango = `${formatearHora24(turno.starts_at)} – ${formatearHora24(turno.ends_at)}`
  return cruza ? `${rango} (día siguiente)` : rango
}

export function agruparTurnos(
  turnos: readonly SlotResponse[],
  claveDe: (turno: SlotResponse) => string,
): ReadonlyMap<string, readonly SlotResponse[]> {
  const grupos = new Map<string, SlotResponse[]>()
  for (const turno of turnos) {
    const clave = claveDe(turno)
    grupos.set(clave, [...(grupos.get(clave) ?? []), turno])
  }
  return grupos
}
