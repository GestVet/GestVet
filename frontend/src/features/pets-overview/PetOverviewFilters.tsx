import FieldIcon from '../../components/FieldIcon'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { NativeSelect, NativeSelectOption } from '../../components/ui/native-select'
import { VACCINATION_STATUSES } from './vaccinationStatus'

export interface PetOverviewFilterValues {
  readonly especie: string
  readonly estado: string
  readonly pesoMin: string
  readonly pesoMax: string
}

interface PetOverviewFiltersProps extends PetOverviewFilterValues {
  readonly especies: readonly string[]
  readonly idPrefix: string
  readonly onChange: (valores: PetOverviewFilterValues) => void
}

export default function PetOverviewFilters({
  especie,
  estado,
  pesoMin,
  pesoMax,
  especies,
  idPrefix,
  onChange,
}: PetOverviewFiltersProps) {
  const valores = { especie, estado, pesoMin, pesoMax }
  const campo =
    (clave: keyof PetOverviewFilterValues) =>
    (evento: { target: { value: string } }): void => {
      onChange({ ...valores, [clave]: evento.target.value })
    }

  return (
    <div className="grid items-end gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor={`${idPrefix}-especie`}>Especie</Label>
        <FieldIcon icon="mascota">
          <NativeSelect
            id={`${idPrefix}-especie`}
            className="w-full [&_select]:h-10"
            value={especie}
            onChange={campo('especie')}
          >
            <NativeSelectOption value="">Todas</NativeSelectOption>
            {especies.map((opcion) => (
              <NativeSelectOption key={opcion} value={opcion}>
                {opcion}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </FieldIcon>
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor={`${idPrefix}-estado`}>Estado de vacunación</Label>
        <FieldIcon icon="salud">
          <NativeSelect
            id={`${idPrefix}-estado`}
            className="w-full [&_select]:h-10"
            value={estado}
            onChange={campo('estado')}
          >
            <NativeSelectOption value="">Todos</NativeSelectOption>
            {VACCINATION_STATUSES.map((opcion) => (
              <NativeSelectOption key={opcion.value} value={opcion.value}>
                {opcion.label}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </FieldIcon>
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor={`${idPrefix}-peso-min`}>Peso mínimo (kg)</Label>
        <Input
          id={`${idPrefix}-peso-min`}
          type="number"
          min={0}
          step="0.1"
          className="h-10"
          value={pesoMin}
          onChange={campo('pesoMin')}
        />
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor={`${idPrefix}-peso-max`}>Peso máximo (kg)</Label>
        <Input
          id={`${idPrefix}-peso-max`}
          type="number"
          min={0}
          step="0.1"
          className="h-10"
          value={pesoMax}
          onChange={campo('pesoMax')}
        />
      </div>
    </div>
  )
}
