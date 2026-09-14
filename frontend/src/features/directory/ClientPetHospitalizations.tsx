import { useQuery } from '@tanstack/react-query'

import { fetchHospitalizations, hospitalizationsQueryKey } from '../../api/hospitalizations'
import HospitalizationList from '../../components/HospitalizationList'
import { useCan } from '../../store/session'

interface ClientPetHospitalizationsProps {
  readonly petId: number
}

export default function ClientPetHospitalizations({ petId }: ClientPetHospitalizationsProps) {
  const puedeGestionar = useCan('hospitalizations.manage')
  const internaciones = useQuery({
    queryKey: hospitalizationsQueryKey(petId),
    queryFn: () => fetchHospitalizations(petId),
  })

  return (
    <HospitalizationList
      items={internaciones.data?.items ?? []}
      isLoading={internaciones.isPending}
      petId={petId}
      canManage={puedeGestionar}
    />
  )
}
