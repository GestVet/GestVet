import { useQuery } from '@tanstack/react-query'

import { fetchMyPets, myPetsQueryKey } from '../../api/pets'
import FormMessage from '../../components/FormMessage'
import PageHeader from '../../components/PageHeader'
import BookingForm from './BookingForm'
import EmergencyPanel from './EmergencyPanel'

export default function BookingView() {
  const mascotas = useQuery({ queryKey: myPetsQueryKey, queryFn: fetchMyPets })
  const sinMascotas =
    !mascotas.isPending && !mascotas.data?.items.some((mascota) => mascota.is_active)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Reservar una cita" />

      {sinMascotas ? (
        <FormMessage tone="error">
          Primero registrá una mascota activa en la sección Mis mascotas.
        </FormMessage>
      ) : null}

      <div className="grid items-start gap-6 lg:grid-cols-[1fr_20rem]">
        <BookingForm />
        <EmergencyPanel />
      </div>
    </div>
  )
}
