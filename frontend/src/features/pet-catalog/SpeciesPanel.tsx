import { addSpecies } from '../../api/pets'
import type { CatalogSpeciesResponse } from '../../api/types'
import FieldIcon from '../../components/FieldIcon'
import SectionCard from '../../components/SectionCard'
import { Button } from '../../components/ui/button'
import { Label } from '../../components/ui/label'
import { NativeSelect, NativeSelectOption } from '../../components/ui/native-select'
import CatalogEntryDialogButton from './CatalogEntryDialogButton'
import { MAX_ESPECIE } from './useCatalogChange'

interface SpeciesPanelProps {
  readonly especies: readonly CatalogSpeciesResponse[]
  readonly isLoading: boolean
  readonly elegidaId: number | undefined
  readonly onElegir: (id: number) => void
}

function razasActivas(especie: CatalogSpeciesResponse): string {
  const cantidad = especie.breeds.filter((raza) => raza.is_active).length
  return cantidad === 1 ? '1 raza' : `${String(cantidad)} razas`
}

/**
 * Las especies: elegir una muestra sus razas.
 *
 * En pantallas anchas es una lista al costado. En el celular, una lista de
 * veinte especies empujaría las razas muy abajo, así que se elige de un select.
 */
export default function SpeciesPanel({ especies, isLoading, elegidaId, onElegir }: SpeciesPanelProps) {
  return (
    <SectionCard
      title="Especies"
      scrollable
      actions={
        <CatalogEntryDialogButton
          id="nueva-especie"
          buttonLabel="Agregar especie"
          buttonIcon="agregar"
          dialogTitle="Agregar una especie"
          dialogDescription="Aparece al instante al registrar mascotas, con la raza «Sin especificar»."
          label="Nombre de la especie"
          placeholder="Petauro del azúcar"
          icon="mascota"
          maxLength={MAX_ESPECIE}
          submitLabel="Agregar especie"
          existing={especies}
          onSave={addSpecies}
        />
      }
    >
      {isLoading ? <p className="m-0 text-sm text-muted-foreground">Cargando especies…</p> : null}
      <div className="flex flex-col gap-2 lg:hidden">
        <Label htmlFor="especie-elegida">Especie</Label>
        <FieldIcon icon="mascota">
          <NativeSelect
            id="especie-elegida"
            className="w-full [&_select]:h-10"
            value={elegidaId === undefined ? '' : String(elegidaId)}
            onChange={(evento) => {
              onElegir(Number(evento.target.value))
            }}
          >
            {especies.map((especie) => (
              <NativeSelectOption key={especie.id} value={String(especie.id)}>
                {`${especie.name}${especie.is_active ? '' : ' (desactivada)'} · ${razasActivas(especie)}`}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </FieldIcon>
      </div>
      <ul className="m-0 hidden list-none flex-col gap-1 p-0 lg:flex">
        {especies.map((especie) => {
          const elegida = especie.id === elegidaId
          return (
            <li key={especie.id}>
              <Button
                type="button"
                variant={elegida ? 'secondary' : 'ghost'}
                aria-pressed={elegida}
                className="h-auto w-full justify-between gap-3 px-3 py-2 font-normal"
                onClick={() => {
                  onElegir(especie.id)
                }}
              >
                <span className={especie.is_active ? 'font-medium' : 'text-muted-foreground line-through'}>
                  {especie.name}
                </span>
                <span className="text-xs text-muted-foreground tabular-nums">{razasActivas(especie)}</span>
              </Button>
            </li>
          )
        })}
      </ul>
    </SectionCard>
  )
}
