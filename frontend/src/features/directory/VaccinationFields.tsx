import type { UseFormReturn } from 'react-hook-form'

import type { VaccineOptionResponse } from '../../api/types'
import SelectField from '../../components/SelectField'
import TextareaField from '../../components/TextareaField'
import TextField from '../../components/TextField'
import { NativeSelectOption } from '../../components/ui/native-select'
import { hoyEnClinica } from '../../services/clinicTime'
import { proximaDosis, type VaccinationFormValues } from './vaccinationSchema'

interface VaccinationFieldsProps {
  readonly form: UseFormReturn<VaccinationFormValues>
  readonly opciones: readonly VaccineOptionResponse[]
  readonly cargando: boolean
  readonly petId: number
}

/** Qué vacuna, cuándo se aplicó, cuándo toca la próxima y con qué producto y lote. */
export default function VaccinationFields({ form, opciones, cargando, petId }: VaccinationFieldsProps) {
  const { register, getValues, setValue, formState } = form
  const errores = formState.errors
  const id = (nombre: string) => `vacuna-${nombre}-${String(petId)}`
  // Al elegir la vacuna o cambiar la fecha, la próxima dosis se recalcula con el
  // intervalo que da el servidor según la especie y la edad.
  const sugerir = () => {
    const { vaccine, applied_on } = getValues()
    const opcion = opciones.find((item) => item.vaccine === vaccine)
    setValue('next_due_on', proximaDosis(applied_on, opcion?.interval_days), {
      shouldDirty: true,
      shouldValidate: formState.isSubmitted,
    })
  }

  return (
    <div className="grid gap-5 sm:grid-cols-2">
      <div className="sm:col-span-2">
        <SelectField
          id={id('tipo')}
          label="Vacuna"
          icon="vacuna"
          placeholder={cargando ? 'Cargando…' : 'Elige una'}
          field={register('vaccine', { onChange: sugerir })}
          error={errores.vaccine?.message}
        >
          {opciones.map((opcion) => (
            <NativeSelectOption key={opcion.vaccine} value={opcion.vaccine}>
              {opcion.label}
            </NativeSelectOption>
          ))}
        </SelectField>
      </div>
      <TextField
        id={id('aplicada')}
        label="Fecha de aplicación"
        type="date"
        max={hoyEnClinica()}
        field={register('applied_on', { onChange: sugerir })}
        error={errores.applied_on?.message}
      />
      <TextField
        id={id('proxima')}
        label="Próxima dosis"
        type="date"
        hint="Sugerida según la vacuna y la edad. Déjala vacía si no lleva refuerzo."
        field={register('next_due_on')}
        error={errores.next_due_on?.message}
      />
      <TextField
        id={id('producto')}
        label="Producto"
        placeholder="Nobivac Rabies"
        icon="tratamiento"
        maxLength={80}
        field={register('product_name')}
        error={errores.product_name?.message}
      />
      <TextField
        id={id('lote')}
        label="Lote"
        placeholder="A123B45"
        icon="numero"
        maxLength={40}
        field={register('batch')}
        error={errores.batch?.message}
      />
      <div className="sm:col-span-2">
        <TextareaField
          id={id('notas')}
          label="Notas (opcional)"
          placeholder="Sin reacciones después de la aplicación"
          icon="nota"
          rows={2}
          field={register('notes')}
          error={errores.notes?.message}
        />
      </div>
    </div>
  )
}
