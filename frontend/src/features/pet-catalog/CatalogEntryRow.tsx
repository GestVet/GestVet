import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import type { IconName } from '../../components/icons'
import StatusBadge from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { errorMessage } from '../../services/api'
import type { NombreDelCatalogo } from '../../services/catalogName'
import CatalogEntryDialogButton from './CatalogEntryDialogButton'
import { useCatalogChange } from './useCatalogChange'

export interface CatalogEntry {
  readonly id: number
  readonly name: string
  readonly is_active: boolean
  readonly is_locked: boolean
}

interface CatalogEntryRowProps {
  readonly entry: CatalogEntry
  /** "especie" o "raza": arma las etiquetas. */
  readonly kind: string
  readonly icon: IconName
  readonly maxLength: number
  /** Las demás especies o razas de la lista, para avisar de parecidos al corregir. */
  readonly siblings: readonly NombreDelCatalogo[]
  readonly onRename: (name: string) => Promise<unknown>
  readonly onToggle: (isActive: boolean) => Promise<unknown>
}

/**
 * Una especie o raza, con sus acciones.
 *
 * Nada se borra: desactivar la saca de los formularios y las mascotas que ya
 * la tienen la conservan. Corregir el nombre lo corrige también en sus fichas.
 */
export default function CatalogEntryRow({
  entry,
  kind,
  icon,
  maxLength,
  siblings,
  onRename,
  onToggle,
}: CatalogEntryRowProps) {
  const cambio = useCatalogChange(onToggle)
  const accion = entry.is_active ? 'Desactivar' : 'Activar'

  return (
    <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className={entry.is_active ? 'font-medium' : 'font-medium text-muted-foreground'}>
          {entry.name}
        </span>
        {entry.is_active ? null : <StatusBadge label="Desactivada" tone="cancelled" />}
        {entry.is_locked ? <StatusBadge label="Fija" tone="confirmed" /> : null}
      </div>
      {entry.is_locked ? null : (
        <div className="flex flex-wrap gap-2">
          <CatalogEntryDialogButton
            id={`corregir-${kind}-${String(entry.id)}`}
            buttonLabel="Corregir"
            buttonAriaLabel={`Corregir ${entry.name}`}
            buttonIcon="nota"
            buttonVariant="outline"
            dialogTitle={`Corregir la ${kind} «${entry.name}»`}
            dialogDescription="El nombre nuevo se corrige también en las fichas de las mascotas que la tienen."
            label="Nombre"
            placeholder={entry.name}
            icon={icon}
            maxLength={maxLength}
            submitLabel="Guardar"
            initialName={entry.name}
            existing={siblings.filter((sibling) => sibling.name !== entry.name)}
            onSave={onRename}
          />
          <Button
            type="button"
            size="sm"
            variant="ghost"
            aria-label={`${accion} ${entry.name}`}
            disabled={cambio.isPending}
            onClick={() => {
              cambio.mutate(!entry.is_active)
            }}
          >
            <Icon name={entry.is_active ? 'cancelar' : 'confirmar'} size={14} />
            <span>{accion}</span>
          </Button>
        </div>
      )}
      {cambio.isError ? (
        <FormMessage tone="error">
          {errorMessage(cambio.error, `No se pudo cambiar la ${kind}.`)}
        </FormMessage>
      ) : null}
    </div>
  )
}
