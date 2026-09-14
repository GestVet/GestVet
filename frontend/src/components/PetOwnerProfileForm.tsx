import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { onSubmit } from '../hooks/formSubmit'
import { usePetOwnerProfileUpdate } from '../hooks/usePetProfile'
import FormMessage from './FormMessage'
import Icon from './Icon'
import PetOwnerProfileFields from './PetOwnerProfileFields'
import { petOwnerProfileSchemaFor, type PetOwnerProfileValues } from './petOwnerProfileSchema'
import { Button } from './ui/button'

interface PetOwnerProfileFormProps {
  readonly petId: number
  readonly species: string
  readonly breed: string
  readonly birthDate: string
  readonly sex: 'male' | 'female' | null
  readonly color: string
  readonly microchipNumber: string
  readonly temperament: string
}

type Cuerpo = Parameters<ReturnType<typeof usePetOwnerProfileUpdate>['mutate']>[0]

function valoresIniciales(props: PetOwnerProfileFormProps): PetOwnerProfileValues {
  return {
    species: props.species,
    breed: props.breed,
    birth_date: props.birthDate,
    sex: props.sex ?? '',
    color: props.color,
    microchip_number: props.microchipNumber,
    temperament: props.temperament,
  }
}

/**
 * Lo que se manda: especie, raza y fecha solo si cambiaron.
 *
 * Una mascota cargada antes del catálogo puede tener una especie escrita a
 * mano. Si el dueño solo corrige el color, no hace falta obligarlo a elegir la
 * especie de la lista.
 */
function cuerpo(valores: PetOwnerProfileValues, props: PetOwnerProfileFormProps): Cuerpo {
  const cambiaEspecie = valores.species !== props.species || valores.breed !== props.breed
  return {
    sex: valores.sex === '' ? null : valores.sex,
    color: valores.color,
    microchip_number: valores.microchip_number,
    temperament: valores.temperament,
    species: cambiaEspecie ? valores.species : null,
    breed: cambiaEspecie ? valores.breed : null,
    birth_date: valores.birth_date === props.birthDate ? null : valores.birth_date,
  }
}

/** Datos que conoce el dueño: especie, raza, nacimiento, sexo, color, microchip y temperamento. */
export default function PetOwnerProfileForm(props: PetOwnerProfileFormProps) {
  const formulario = useForm<PetOwnerProfileValues>({
    resolver: zodResolver(petOwnerProfileSchemaFor(props.microchipNumber)),
    defaultValues: valoresIniciales(props),
  })
  const guardar = usePetOwnerProfileUpdate(props.petId)

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        formulario.handleSubmit((valores) => {
          guardar.mutate(cuerpo(valores, props))
        }),
      )}
    >
      <PetOwnerProfileFields formulario={formulario} petId={props.petId} />

      {guardar.isError ? <FormMessage tone="error">{guardar.errorMessage}</FormMessage> : null}

      <Button type="submit" className="self-start" disabled={guardar.isPending}>
        <Icon name="confirmar" size={16} />
        <span>{guardar.isPending ? 'Guardando…' : 'Guardar ficha'}</span>
      </Button>
    </form>
  )
}
