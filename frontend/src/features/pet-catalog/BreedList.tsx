import { useState } from 'react'

import { updateBreed } from '../../api/pets'
import type { CatalogSpeciesResponse } from '../../api/types'
import EmptyState from '../../components/EmptyState'
import FieldIcon from '../../components/FieldIcon'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { claveDeCatalogo } from '../../services/catalogName'
import CatalogEntryRow from './CatalogEntryRow'
import { MAX_RAZA } from './useCatalogChange'

interface BreedListProps {
  readonly especie: CatalogSpeciesResponse
}

/** Las razas de una especie, con un buscador: un perro tiene más de setenta. */
export default function BreedList({ especie }: BreedListProps) {
  const [busqueda, setBusqueda] = useState('')
  const clave = claveDeCatalogo(busqueda)
  const visibles =
    clave === ''
      ? especie.breeds
      : especie.breeds.filter((raza) => claveDeCatalogo(raza.name).includes(clave))
  const idBusqueda = `buscar-raza-${String(especie.id)}`

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-2">
        <Label htmlFor={idBusqueda}>Buscar raza</Label>
        <FieldIcon icon="buscar">
          <Input
            id={idBusqueda}
            type="search"
            className="h-10"
            placeholder="Escribe parte del nombre"
            value={busqueda}
            onChange={(evento) => {
              setBusqueda(evento.target.value)
            }}
          />
        </FieldIcon>
      </div>
      <p className="m-0 text-sm text-muted-foreground" aria-live="polite">
        {clave === ''
          ? `${String(especie.breeds.length)} razas`
          : `${String(visibles.length)} de ${String(especie.breeds.length)} razas`}
      </p>
      {visibles.length === 0 ? (
        <EmptyState title="Ninguna raza coincide con la búsqueda." />
      ) : (
        <ul className="m-0 flex list-none flex-col divide-y p-0">
          {visibles.map((raza) => (
            <li key={raza.id} className="py-3">
              <CatalogEntryRow
                entry={raza}
                kind="raza"
                icon="raza"
                maxLength={MAX_RAZA}
                siblings={especie.breeds}
                onRename={(name) => updateBreed(raza.id, { name, is_active: raza.is_active })}
                onToggle={(isActive) => updateBreed(raza.id, { name: raza.name, is_active: isActive })}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
