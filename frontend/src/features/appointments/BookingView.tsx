import { useQuery } from '@tanstack/react-query'

import { fetchMyPets, myPetsQueryKey } from '../../api/pets'
import FormMessage from '../../components/FormMessage'
import BookingForm from './BookingForm'
import EmergencyPanel from './EmergencyPanel'

export default function BookingView() {
  const mascotas = useQuery({ queryKey: myPetsQueryKey, queryFn: fetchMyPets })
  const sinMascotas =
    !mascotas.isPending && !mascotas.data?.items.some((mascota) => mascota.is_active)

  return (
    <div className="stack">
      <div className="page-header">
        <h1>Reservar una cita</h1>
      </div>

      {sinMascotas ? (
        <FormMessage tone="error">
          Primero registrá una mascota activa en la sección Mis mascotas.
        </FormMessage>
      ) : null}

      <BookingForm />
      <EmergencyPanel />
    </div>
  )
}
