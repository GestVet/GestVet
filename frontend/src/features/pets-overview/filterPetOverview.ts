import type { PetOverviewResponse } from '../../api/types'
import type { BarChartDatum } from '../../components/charts/BarChart'
import type { PetOverviewFilterValues } from './PetOverviewFilters'
import { VACCINATION_STATUSES } from './vaccinationStatus'

function pesoDentroDelRango(pesoKg: string | null, min: number | null, max: number | null): boolean {
  if (min === null && max === null) {
    return true
  }
  const peso = pesoKg === null ? null : Number(pesoKg)
  if (peso === null) {
    return false
  }
  return (min === null || peso >= min) && (max === null || peso <= max)
}

export function filterPetOverview(
  items: readonly PetOverviewResponse[],
  filtros: PetOverviewFilterValues,
): PetOverviewResponse[] {
  const pesoMin = filtros.pesoMin === '' ? null : Number(filtros.pesoMin)
  const pesoMax = filtros.pesoMax === '' ? null : Number(filtros.pesoMax)
  return items.filter(
    (item) =>
      (filtros.especie === '' || item.species === filtros.especie) &&
      (filtros.estado === '' || item.vaccination_status === filtros.estado) &&
      pesoDentroDelRango(item.weight_kg, pesoMin, pesoMax),
  )
}

export function speciesChartData(items: readonly PetOverviewResponse[]): BarChartDatum[] {
  const conteos = new Map<string, number>()
  for (const item of items) {
    conteos.set(item.species, (conteos.get(item.species) ?? 0) + 1)
  }
  return [...conteos.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([label, value]) => ({ label, value, color: 'var(--chart-1)' }))
}

export function vaccinationStatusChartData(items: readonly PetOverviewResponse[]): BarChartDatum[] {
  const conteos = new Map(VACCINATION_STATUSES.map((estado) => [estado.value, 0]))
  for (const item of items) {
    conteos.set(item.vaccination_status, (conteos.get(item.vaccination_status) ?? 0) + 1)
  }
  return VACCINATION_STATUSES.map((estado) => ({
    label: estado.label,
    value: conteos.get(estado.value) ?? 0,
    color: estado.color,
  }))
}
