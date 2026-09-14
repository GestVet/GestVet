import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { fetchManagedCatalog, managedCatalogQueryKey } from '../../api/pets'
import PageHeader from '../../components/PageHeader'
import BreedsPanel from './BreedsPanel'
import SpeciesPanel from './SpeciesPanel'

/**
 * Especies y razas de la clínica.
 *
 * Cuando llega un animal que no está en la lista, la administración lo agrega
 * acá y aparece en el momento en todos los formularios de mascotas. Cada
 * nombre se guarda con el mismo formato, sin importar cómo se escriba.
 */
export default function PetCatalogView() {
  const catalogo = useQuery({ queryKey: managedCatalogQueryKey, queryFn: fetchManagedCatalog })
  const [elegidaId, setElegidaId] = useState<number | null>(null)
  const especies = catalogo.data?.species ?? []
  const elegida = especies.find((especie) => especie.id === elegidaId) ?? especies.at(0)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Especies y razas"
        description="Lo que se elige al registrar una mascota. Si llega un animal que no está, agrégalo y aparece al instante en todos los formularios."
      />
      <div className="grid gap-6 lg:grid-cols-[20rem_minmax(0,1fr)] lg:items-start">
        <SpeciesPanel
          especies={especies}
          isLoading={catalogo.isPending}
          elegidaId={elegida?.id}
          onElegir={setElegidaId}
        />
        {elegida === undefined ? null : <BreedsPanel key={elegida.id} especie={elegida} especies={especies} />}
      </div>
    </div>
  )
}
