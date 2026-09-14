import { Button } from './ui/button'

interface RowExpandButtonProps {
  readonly isExpanded: boolean
  readonly onToggle: () => void
  readonly collapsedLabel: string
  readonly expandedLabel: string
}

/**
 * El boton que despliega el detalle de una fila.
 *
 * `aria-expanded` le dice al lector de pantalla si el detalle esta abierto,
 * ademas del texto, que cambia.
 */
export default function RowExpandButton({
  isExpanded,
  onToggle,
  collapsedLabel,
  expandedLabel,
}: RowExpandButtonProps) {
  return (
    <Button type="button" variant="outline" size="sm" aria-expanded={isExpanded} onClick={onToggle}>
      {isExpanded ? expandedLabel : collapsedLabel}
    </Button>
  )
}
