import type { UseFormReturn } from 'react-hook-form'

import type { PetOwnerProfileValues } from './petOwnerProfileSchema'
import SelectField from './SelectField'
import TextField from './TextField'
import { NativeSelectOption } from './ui/native-select'

interface PetOwnerClinicalFieldsProps {
  readonly formulario: UseFormReturn<PetOwnerProfileValues>
  readonly petId: number
}

/** Peso, altura y esterilización: el dueño los carga si los sabe; el veterinario los confirma o corrige en consulta. */
export default function PetOwnerClinicalFields({ formulario, petId }: PetOwnerClinicalFieldsProps) {
  const { register, formState } = formulario
  const errores = formState.errors
  const id = (campo: string) => `${campo}-${String(petId)}`

  return (
    <>
      <TextField
        id={id('weight_kg')}
        label="Peso (kg)"
        placeholder="12.5"
        icon="peso"
        type="number"
        inputMode="decimal"
        step="0.1"
        min="0"
        field={register('weight_kg')}
        error={errores.weight_kg?.message}
      />
      <TextField
        id={id('height_cm')}
        label="Altura (cm)"
        placeholder="45"
        icon="altura"
        type="number"
        inputMode="decimal"
        step="0.1"
        min="0"
        field={register('height_cm')}
        error={errores.height_cm?.message}
      />
      <SelectField
        id={id('is_sterilized')}
        label="Esterilizado"
        icon="salud"
        field={register('is_sterilized')}
        placeholder="No evaluado"
      >
        <NativeSelectOption value="true">Sí</NativeSelectOption>
        <NativeSelectOption value="false">No</NativeSelectOption>
      </SelectField>
    </>
  )
}
