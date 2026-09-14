import { type Control, useController } from 'react-hook-form'

import FieldError from '../../components/FieldError'
import { Button } from '../../components/ui/button'
import { Checkbox } from '../../components/ui/checkbox'
import { Label } from '../../components/ui/label'
import { NOMBRES_DE_DIAS, type WeeklyPlanFormValues } from './weeklyPlanSchema'

const ATAJOS: readonly { readonly label: string; readonly dias: readonly number[] }[] = [
  { label: 'Lunes a viernes', dias: [0, 1, 2, 3, 4] },
  { label: 'Lunes a sábado', dias: [0, 1, 2, 3, 4, 5] },
  { label: 'Todos', dias: [0, 1, 2, 3, 4, 5, 6] },
]

interface WeekdayPickerProps {
  readonly control: Control<WeeklyPlanFormValues>
}

/** Los días del horario, con atajos para las combinaciones de siempre. */
export default function WeekdayPicker({ control }: WeekdayPickerProps) {
  const { field, fieldState } = useController({ control, name: 'weekdays' })
  const alternar = (dia: number, marcado: boolean) => {
    const resto = field.value.filter((elegido) => elegido !== dia)
    field.onChange(marcado ? [...resto, dia].sort((a, b) => a - b) : resto)
  }

  return (
    <fieldset
      className="m-0 flex flex-col gap-3 border-0 p-0 sm:col-span-2"
      aria-describedby={fieldState.error === undefined ? undefined : 'plan-dias-error'}
    >
      <legend className="mb-2 text-sm font-medium">Días</legend>
      <div className="flex flex-wrap gap-2">
        {ATAJOS.map((atajo) => (
          <Button
            key={atajo.label}
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              field.onChange([...atajo.dias])
            }}
          >
            {atajo.label}
          </Button>
        ))}
      </div>
      <div className="flex flex-wrap gap-x-5 gap-y-2">
        {NOMBRES_DE_DIAS.map((nombre, dia) => {
          const id = `plan-dia-${String(dia)}`
          return (
            <div key={nombre} className="flex items-center gap-2">
              <Checkbox
                id={id}
                checked={field.value.includes(dia)}
                onCheckedChange={(marcado) => {
                  alternar(dia, marcado === true)
                }}
              />
              <Label htmlFor={id} className="font-normal">
                {nombre}
              </Label>
            </div>
          )
        })}
      </div>
      <FieldError id="plan-dias-error" message={fieldState.error?.message} />
    </fieldset>
  )
}
