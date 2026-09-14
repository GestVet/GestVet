import { type UseFormReturn, useWatch } from 'react-hook-form'

import { limitesDeNacimiento, soloDigitosDeMicrochip } from './formRules'
import { MAX_COLOR, MAX_TEMPERAMENTO, type PetOwnerProfileValues } from './petOwnerProfileSchema'
import SelectField from './SelectField'
import SpeciesBreedFields from './SpeciesBreedFields'
import TextField from './TextField'
import { NativeSelectOption } from './ui/native-select'

interface PetOwnerProfileFieldsProps {
  readonly formulario: UseFormReturn<PetOwnerProfileValues>
  readonly petId: number
}

export default function PetOwnerProfileFields({ formulario, petId }: PetOwnerProfileFieldsProps) {
  const { register, control, setValue, formState } = formulario
  const especie = useWatch({ control, name: 'species' })
  const errores = formState.errors
  const limites = limitesDeNacimiento()
  const id = (campo: string) => `${campo}-${String(petId)}`

  return (
    <div className="grid gap-5 sm:grid-cols-2">
      <SpeciesBreedFields
        idPrefix={id('ficha')}
        species={especie}
        speciesField={register('species', {
          onChange: () => {
            setValue('breed', '')
          },
        })}
        speciesError={errores.species?.message}
        breedField={register('breed')}
        breedError={errores.breed?.message}
      />
      <TextField
        id={id('birth_date')}
        label="Fecha de nacimiento"
        type="date"
        min={limites.min}
        max={limites.max}
        field={register('birth_date')}
        error={errores.birth_date?.message}
      />
      <SelectField id={id('sex')} label="Sexo" field={register('sex')} placeholder="No especificado">
        <NativeSelectOption value="male">Macho</NativeSelectOption>
        <NativeSelectOption value="female">Hembra</NativeSelectOption>
      </SelectField>
      <TextField
        id={id('color')}
        label="Color"
        maxLength={MAX_COLOR}
        field={register('color')}
        error={errores.color?.message}
      />
      <TextField
        id={id('microchip')}
        label="Microchip"
        inputMode="numeric"
        maxLength={15}
        hint="De 9 a 15 dígitos. Déjalo vacío si no tiene."
        sanitize={soloDigitosDeMicrochip}
        field={register('microchip_number')}
        error={errores.microchip_number?.message}
      />
      <TextField
        id={id('temperament')}
        label="Temperamento"
        maxLength={MAX_TEMPERAMENTO}
        placeholder="Por ejemplo: tranquilo, nervioso con extraños"
        field={register('temperament')}
        error={errores.temperament?.message}
      />
    </div>
  )
}
