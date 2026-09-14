import { Badge } from './ui/badge'

export type StatusTone = 'pending' | 'confirmed' | 'completed' | 'cancelled'

// Cada tono lleva su propio texto oscuro sobre un fondo claro del mismo color,
// con contraste AA. El estado siempre esta escrito: el color acompana.
const TONE_CLASSES: Record<StatusTone, string> = {
  pending: 'bg-warning/10 text-warning',
  confirmed: 'bg-secondary text-secondary-foreground',
  completed: 'bg-success/10 text-success',
  cancelled: 'bg-destructive/10 text-destructive',
}

interface StatusBadgeProps {
  readonly label: string
  /** Sin tono, la etiqueta es neutra. */
  readonly tone?: StatusTone
}

export default function StatusBadge({ label, tone }: StatusBadgeProps) {
  if (tone === undefined) {
    return <Badge variant="outline">{label}</Badge>
  }
  return <Badge className={TONE_CLASSES[tone]}>{label}</Badge>
}
