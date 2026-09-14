import { addBreed, updateSpecies } from '../../api/pets'
import type { CatalogSpeciesResponse } from '../../api/types'
import SectionCard from '../../components/SectionCard'
import { Separator } from '../../components/ui/separator'
import BreedList from './BreedList'
import CatalogEntryDialogButton from './CatalogEntryDialogButton'
import CatalogEntryRow from './CatalogEntryRow'
import { MAX_ESPECIE, MAX_RAZA } from './useCatalogChange'

interface BreedsPanelProps {
  readonly especie: CatalogSpeciesResponse
  /** Todas las especies, para avisar de parecidos al corregir el nombre de esta. */
  readonly especies: readonly CatalogSpeciesResponse[]
}

/** Una especie y sus razas: corregir la especie, agregar razas y administrarlas. */
export default function BreedsPanel({ especie, especies }: BreedsPanelProps) {
  return (
    <SectionCard
      title={`Razas de ${especie.name}`}
      description={
        especie.is_active
          ? 'Las razas desactivadas no aparecen al registrar una mascota, pero las fichas que ya las tienen las conservan.'
          : 'Esta especie está desactivada: no aparece al registrar una mascota.'
      }
      actions={
        <CatalogEntryDialogButton
          id={`nueva-raza-${String(especie.id)}`}
          buttonLabel="Agregar raza"
          buttonIcon="agregar"
          dialogTitle={`Agregar una raza de ${especie.name}`}
          dialogDescription="Aparece al instante al registrar mascotas de esta especie."
          label="Nombre de la raza"
          placeholder="Border terrier"
          icon="raza"
          maxLength={MAX_RAZA}
          submitLabel="Agregar raza"
          existing={especie.breeds}
          onSave={(name) => addBreed(especie.id, name)}
        />
      }
    >
      <CatalogEntryRow
        entry={{ ...especie, is_locked: false }}
        kind="especie"
        icon="mascota"
        maxLength={MAX_ESPECIE}
        siblings={especies}
        onRename={(name) => updateSpecies(especie.id, { name, is_active: especie.is_active })}
        onToggle={(isActive) => updateSpecies(especie.id, { name: especie.name, is_active: isActive })}
      />
      <Separator />
      <BreedList especie={especie} />
    </SectionCard>
  )
}
