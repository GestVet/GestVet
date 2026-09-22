import { useQuery } from '@tanstack/react-query'
import type { UseFormRegister } from 'react-hook-form'

import { fetchMyPets, myPetsQueryKey } from '../../api/pets'
import SelectField from '../../components/SelectField'
import { NativeSelectOption } from '../../components/ui/native-select'
import type { BookingForm } from './bookingSchema'

interface PetSelectFieldProps {
  readonly register: UseFormRegister<BookingForm>
  readonly error: string | undefined
}

/** La mascota para la que se reserva, entre las propias que siguen activas. */
export default function PetSelectField({ register, error }: PetSelectFieldProps) {
  const mascotas = useQuery({ queryKey: myPetsQueryKey, queryFn: fetchMyPets })
  const activas = mascotas.data?.items.filter((mascota) => mascota.is_active) ?? []

  return (
    <SelectField
      id="pet_id"
      label="Mascota"
      icon="mascota"
      placeholder="Elige una"
      field={register('pet_id')}
      error={error}
    >
      {activas.map((mascota) => (
        <NativeSelectOption key={mascota.id} value={mascota.id}>
          {mascota.name} · {mascota.species}
        </NativeSelectOption>
      ))}
    </SelectField>
  )
}
