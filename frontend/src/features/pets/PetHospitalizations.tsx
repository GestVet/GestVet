import { useQuery } from '@tanstack/react-query'

import { fetchHospitalizations, hospitalizationsQueryKey } from '../../api/hospitalizations'
import HospitalizationList from '../../components/HospitalizationList'

interface PetHospitalizationsProps {
  readonly petId: number
}

export default function PetHospitalizations({ petId }: PetHospitalizationsProps) {
  const internaciones = useQuery({
    queryKey: hospitalizationsQueryKey(petId),
    queryFn: () => fetchHospitalizations(petId),
  })

  return (
    <HospitalizationList
      items={internaciones.data?.items ?? []}
      isLoading={internaciones.isPending}
      petId={petId}
      canManage={false}
    />
  )
}
