import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { onSubmit } from '../hooks/formSubmit'
import { usePetOwnerProfileUpdate } from '../hooks/usePetProfile'
import FormMessage from './FormMessage'
import Icon from './Icon'
import SelectField from './SelectField'
import TextField from './TextField'

const esquema = z.object({
  sex: z.enum(['', 'male', 'female']),
  color: z.string().max(80),
  microchip_number: z.string().max(40),
  temperament: z.string().max(120),
})

type Formulario = z.infer<typeof esquema>

interface PetOwnerProfileFormProps {
  readonly petId: number
  readonly sex: 'male' | 'female' | null
  readonly color: string
  readonly microchipNumber: string
  readonly temperament: string
}

function valoresIniciales(props: PetOwnerProfileFormProps): Formulario {
  return {
    sex: props.sex ?? '',
    color: props.color,
    microchip_number: props.microchipNumber,
    temperament: props.temperament,
  }
}

/** Datos que conoce el dueño: sexo, color, microchip y temperamento. */
export default function PetOwnerProfileForm(props: PetOwnerProfileFormProps) {
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: valoresIniciales(props),
  })
  const guardar = usePetOwnerProfileUpdate(props.petId)
  const errores = formState.errors

  return (
    <form
      className="form"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          guardar.mutate({
            sex: valores.sex === '' ? null : valores.sex,
            color: valores.color,
            microchip_number: valores.microchip_number,
            temperament: valores.temperament,
          })
        }),
      )}
    >
      <SelectField id="sex" label="Sexo" field={register('sex')} placeholder="No especificado">
        <option value="male">Macho</option>
        <option value="female">Hembra</option>
      </SelectField>
      <TextField id="color" label="Color" field={register('color')} error={errores.color?.message} />
      <TextField
        id="microchip_number"
        label="Microchip"
        field={register('microchip_number')}
        error={errores.microchip_number?.message}
      />
      <TextField
        id="temperament"
        label="Temperamento"
        field={register('temperament')}
        error={errores.temperament?.message}
      />

      {guardar.isError ? <FormMessage tone="error">{guardar.errorMessage}</FormMessage> : null}

      <button type="submit" className="btn btn-blue" disabled={guardar.isPending}>
        <Icon name="confirmar" size={16} />
        <span>{guardar.isPending ? 'Guardando…' : 'Guardar'}</span>
      </button>
    </form>
  )
}
