import type { UseFormRegisterReturn } from 'react-hook-form'

import { usePetCatalog } from '../hooks/usePetCatalog'
import SelectField from './SelectField'
import { NativeSelectOption } from './ui/native-select'

interface SpeciesBreedFieldsProps {
  /** Prefijo de los `id`, para usar el par más de una vez en la misma página. */
  readonly idPrefix: string
  readonly species: string
  readonly speciesField: UseFormRegisterReturn
  readonly speciesError?: string
  /** Sin campo de raza, solo se pide la especie. */
  readonly breedField?: UseFormRegisterReturn
  readonly breedError?: string
}

/**
 * Especie y raza, elegidas de la lista del servidor.
 *
 * Reemplaza a dos campos de texto libre: "perro", "Perro" y "can" eran tres
 * especies distintas para cualquier búsqueda. La raza depende de la especie,
 * así que su lista aparece recién cuando hay especie elegida.
 */
export default function SpeciesBreedFields({
  idPrefix,
  species,
  speciesField,
  speciesError,
  breedField,
  breedError,
}: SpeciesBreedFieldsProps) {
  const { especies, razasDe, isPending } = usePetCatalog()
  const razas = razasDe(species)

  return (
    <>
      <SelectField
        id={`${idPrefix}-species`}
        label="Especie"
        icon="mascota"
        placeholder={isPending ? 'Cargando…' : 'Elige una'}
        field={speciesField}
        error={speciesError}
      >
        {especies.map((especie) => (
          <NativeSelectOption key={especie.name} value={especie.name}>
            {especie.name}
          </NativeSelectOption>
        ))}
      </SelectField>
      {breedField === undefined ? null : (
        <SelectField
          id={`${idPrefix}-breed`}
          label="Raza"
          icon="raza"
          placeholder={species === '' ? 'Primero elige la especie' : 'Elige una'}
          hint="Si no la sabes, elige «Sin especificar»."
          field={breedField}
          error={breedError}
        >
          {razas.map((raza) => (
            <NativeSelectOption key={raza} value={raza}>
              {raza}
            </NativeSelectOption>
          ))}
        </SelectField>
      )}
    </>
  )
}
