import { useMemo, useState } from 'react'

import type { PetOverviewResponse } from '../../api/types'
import BarChart from '../../components/charts/BarChart'
import DataTable, { type DataColumn } from '../../components/DataTable'
import SectionCard from '../../components/SectionCard'
import { filterPetOverview, speciesChartData, vaccinationStatusChartData } from './filterPetOverview'
import PetOverviewFilters, { type PetOverviewFilterValues } from './PetOverviewFilters'
import { vaccinationStatusMeta } from './vaccinationStatus'

const SIN_FILTROS: PetOverviewFilterValues = {
  especie: '',
  estado: '',
  pesoMin: '',
  pesoMax: '',
}

const COLUMNAS: readonly DataColumn<PetOverviewResponse>[] = [
  { id: 'mascota', header: 'Mascota', cell: (item) => item.pet_name },
  { id: 'dueno', header: 'Dueño', cell: (item) => item.owner_name },
  { id: 'especie', header: 'Especie', cell: (item) => item.species },
  { id: 'raza', header: 'Raza', cell: (item) => item.breed },
  { id: 'sexo', header: 'Sexo', cell: (item) => item.sex_label },
  { id: 'edad', header: 'Edad', cell: (item) => `${String(item.age_years)} años` },
  { id: 'peso', header: 'Peso', cell: (item) => (item.weight_kg === null ? '—' : `${item.weight_kg} kg`) },
  {
    id: 'vacunacion',
    header: 'Estado de vacunación',
    cell: (item) => (
      <span className={vaccinationStatusMeta(item.vaccination_status).textClassName}>
        {item.vaccination_status_label}
      </span>
    ),
  },
]

interface PetOverviewSectionProps {
  readonly titulo: string
  readonly descripcion: string
  readonly items: readonly PetOverviewResponse[]
  readonly idPrefix: string
  readonly collapsible?: boolean
  readonly defaultOpen?: boolean
}

export default function PetOverviewSection({
  titulo,
  descripcion,
  items,
  idPrefix,
  collapsible = false,
  defaultOpen = true,
}: PetOverviewSectionProps) {
  const [filtros, setFiltros] = useState(SIN_FILTROS)

  const especies = useMemo(
    () => [...new Set(items.map((item) => item.species))].sort((a, b) => a.localeCompare(b)),
    [items],
  )

  const filtrados = useMemo(() => filterPetOverview(items, filtros), [items, filtros])
  const porEspecie = useMemo(() => speciesChartData(filtrados), [filtrados])
  const porVacunacion = useMemo(() => vaccinationStatusChartData(filtrados), [filtrados])

  return (
    <SectionCard
      title={titulo}
      description={descripcion}
      collapsible={collapsible}
      defaultOpen={defaultOpen}
    >
      <div className="flex flex-col gap-4">
        <PetOverviewFilters
          {...filtros}
          especies={especies}
          idPrefix={idPrefix}
          onChange={setFiltros}
        />
        <DataTable
          columns={COLUMNAS}
          data={filtrados}
          isLoading={false}
          emptyMessage="Ninguna mascota coincide con los filtros."
          getRowId={(item) => String(item.pet_id)}
          pageSize={10}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <BarChart
            title="Mascotas por especie"
            data={porEspecie}
            emptyMessage="No hay mascotas para graficar."
          />
          <BarChart
            title="Estado de vacunación"
            data={porVacunacion}
            emptyMessage="No hay mascotas para graficar."
          />
        </div>
      </div>
    </SectionCard>
  )
}
