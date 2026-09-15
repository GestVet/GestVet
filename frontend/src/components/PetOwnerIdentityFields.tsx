import { type UseFormReturn, useWatch } from 'react-hook-form'

import { limitesDeNacimiento, soloDigitosDeMicrochip } from './formRules'
import { MAX_COLOR, MAX_TEMPERAMENTO, type PetOwnerProfileValues } from './petOwnerProfileSchema'
import SelectField from './SelectField'
import SpeciesBreedFields from './SpeciesBreedFields'
import TextField from './TextField'
import { NativeSelectOption } from './ui/native-select'

interface PetOwnerIdentityFieldsProps {
  readonly formulario: UseFormReturn<PetOwnerProfileValues>
  readonly petId: number
}

/** Especie, raza, nacimiento, sexo, color, microchip y temperamento: lo que el dueño conoce de memoria. */
export default function PetOwnerIdentityFields({ formulario, petId }: PetOwnerIdentityFieldsProps) {
  const { register, control, setValue, formState } = formulario
  const especie = useWatch({ control, name: 'species' })
  const errores = formState.errors
  const limites = limitesDeNacimiento()
  const id = (campo: string) => `${campo}-${String(petId)}`

  return (
    <>
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
      <SelectField id={id('sex')} label="Sexo" icon="sexo" field={register('sex')} placeholder="No especificado">
        <NativeSelectOption value="male">Macho</NativeSelectOption>
        <NativeSelectOption value="female">Hembra</NativeSelectOption>
      </SelectField>
      <TextField
        id={id('color')}
        label="Color"
        placeholder="Negro con manchas blancas"
        icon="color"
        maxLength={MAX_COLOR}
        field={register('color')}
        error={errores.color?.message}
      />
      <TextField
        id={id('microchip')}
        label="Microchip"
        placeholder="985141000123456"
        icon="microchip"
        inputMode="numeric"
        maxLength={15}
        hint="15 dígitos, estándar ISO. Déjalo vacío si no tiene."
        sanitize={soloDigitosDeMicrochip}
        field={register('microchip_number')}
        error={errores.microchip_number?.message}
      />
      <TextField
        id={id('temperament')}
        label="Temperamento"
        icon="temperamento"
        maxLength={MAX_TEMPERAMENTO}
        placeholder="Tranquilo, nervioso con extraños"
        field={register('temperament')}
        error={errores.temperament?.message}
      />
    </>
  )
}
