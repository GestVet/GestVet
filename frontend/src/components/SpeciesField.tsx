import { useState } from 'react'
import type { ChangeHandler, UseFormRegisterReturn } from 'react-hook-form'

import { COMMON_PET_SPECIES, OTHER_SPECIES_OPTION } from './petSpecies'
import SelectField from './SelectField'
import TextField from './TextField'

interface SpeciesFieldProps {
  readonly speciesId: string
  readonly otherId: string
  readonly speciesField: UseFormRegisterReturn
  readonly otherField: UseFormRegisterReturn
  readonly speciesError?: string
  readonly otherError?: string
  readonly initiallyOther: boolean
}

/**
 * Selector de especie con salida a texto libre.
 *
 * La lista cubre lo más común; "Otro" revela un campo de texto para lo que no
 * está en la lista. El estado de si está elegido "Otro" vive acá, en
 * `useState`, y no en `watch()` de react-hook-form: `watch` devuelve una
 * función nueva en cada render que el compilador de React no puede
 * memoizar con seguridad.
 */
export default function SpeciesField({
  speciesId,
  otherId,
  speciesField,
  otherField,
  speciesError,
  otherError,
  initiallyOther,
}: SpeciesFieldProps) {
  const [esOtro, setEsOtro] = useState(initiallyOther)

  return (
    <>
      <SelectField
        id={speciesId}
        label="Especie"
        error={speciesError}
        placeholder="Elegí una especie"
        field={{
          ...speciesField,
          onChange: ((evento) => {
            setEsOtro((evento.target as HTMLSelectElement).value === OTHER_SPECIES_OPTION)
            return speciesField.onChange(evento)
          }) satisfies ChangeHandler,
        }}
      >
        {COMMON_PET_SPECIES.map((especie) => (
          <option key={especie} value={especie}>
            {especie}
          </option>
        ))}
        <option value={OTHER_SPECIES_OPTION}>{OTHER_SPECIES_OPTION}</option>
      </SelectField>

      {esOtro ? (
        <TextField id={otherId} label="¿Cuál especie?" field={otherField} error={otherError} />
      ) : null}
    </>
  )
}
