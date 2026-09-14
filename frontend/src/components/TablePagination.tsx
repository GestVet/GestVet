import Icon from './Icon'
import { Button } from './ui/button'

interface TablePaginationProps {
  /** Página actual, desde cero. */
  readonly actual: number
  readonly total: number
  readonly onChange: (pagina: number) => void
}

/** Anterior y siguiente, con la página en la que se está anunciada al cambiar. */
export default function TablePagination({ actual, total, onChange }: TablePaginationProps) {
  return (
    <nav aria-label="Paginación" className="flex flex-wrap items-center justify-between gap-3">
      <p className="m-0 text-sm text-muted-foreground" aria-live="polite">
        Página {actual + 1} de {total}
      </p>
      <div className="flex gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={actual === 0}
          onClick={() => {
            onChange(actual - 1)
          }}
        >
          <Icon name="anterior" size={14} />
          <span>Anterior</span>
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={actual >= total - 1}
          onClick={() => {
            onChange(actual + 1)
          }}
        >
          <span>Siguiente</span>
          <Icon name="siguiente" size={14} />
        </Button>
      </div>
    </nav>
  )
}
