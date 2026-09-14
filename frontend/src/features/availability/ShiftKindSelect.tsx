import type { UseFormRegisterReturn } from 'react-hook-form'

import SelectField from '../../components/SelectField'
import { NativeSelectOption } from '../../components/ui/native-select'

interface ShiftKindSelectProps {
  readonly id: string
  readonly field: UseFormRegisterReturn
}

export default function ShiftKindSelect({ id, field }: ShiftKindSelectProps) {
  return (
    <SelectField
      id={id}
      label="Tipo"
      hint="En atención recibe citas. En guardia cubre las emergencias y puede pasar la medianoche."
      field={field}
    >
      <NativeSelectOption value="regular">Atención</NativeSelectOption>
      <NativeSelectOption value="on_call">Guardia</NativeSelectOption>
    </SelectField>
  )
}
