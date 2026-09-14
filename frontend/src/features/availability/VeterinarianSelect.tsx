import type { UseFormRegisterReturn } from 'react-hook-form'

import type { UserResponse } from '../../api/types'
import SelectField from '../../components/SelectField'
import { NativeSelectOption } from '../../components/ui/native-select'

interface VeterinarianSelectProps {
  readonly id: string
  readonly veterinarios: readonly UserResponse[]
  readonly field: UseFormRegisterReturn
  readonly error?: string
}

export default function VeterinarianSelect({
  id,
  veterinarios,
  field,
  error,
}: VeterinarianSelectProps) {
  return (
    <SelectField id={id} label="Veterinario" placeholder="Elige a quién" field={field} error={error}>
      {veterinarios.map((veterinario) => (
        <NativeSelectOption key={veterinario.id} value={String(veterinario.id)}>
          {`${veterinario.first_name} ${veterinario.last_name}`}
        </NativeSelectOption>
      ))}
    </SelectField>
  )
}
