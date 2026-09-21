import Icon from '../../components/Icon'
import SortableList from '../../components/SortableList'
import { useLayoutStore } from '../../store/layout'
import type { NavEntry } from './navigation'

interface NavListEditableProps {
  readonly entries: readonly NavEntry[]
}

const FILA =
  'flex min-h-10 w-full min-w-0 items-center gap-3 rounded-lg border border-dashed border-input bg-card px-3 py-2 text-sm font-medium'

/**
 * El menu en modo de edicion.
 *
 * Las entradas dejan de navegar: son filas que se arrastran o se mueven con
 * los botones. Cada movimiento guarda la lista completa, que es lo que espera
 * la API: el orden entero del menu, no el de una entrada. La etiqueta se
 * envuelve en vez de recortarse: en el sidebar un nombre largo, como
 * "Emergencia (cliente nuevo)", tiene que leerse entero.
 */
export default function NavListEditable({ entries }: NavListEditableProps) {
  const setSidebarOrder = useLayoutStore((state) => state.setSidebarOrder)

  return (
    <SortableList
      items={entries}
      getId={(entry) => entry.to}
      getLabel={(entry) => entry.label}
      onReorder={setSidebarOrder}
      className="m-0 flex list-none flex-col gap-1 p-0"
      renderItem={(entry) => (
        <span className={FILA}>
          <Icon className="shrink-0" name={entry.icon} size={18} />
          <span className="min-w-0 text-pretty break-words">{entry.label}</span>
        </span>
      )}
    />
  )
}
