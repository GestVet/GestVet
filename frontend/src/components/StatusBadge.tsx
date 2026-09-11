interface StatusBadgeProps {
  readonly label: string
  /** Sufijo de la clase, por ejemplo "pending" o "completed". Sin el, neutro. */
  readonly tone?: string
}

export default function StatusBadge({ label, tone }: StatusBadgeProps) {
  return <span className={tone === undefined ? 'badge' : `badge badge-${tone}`}>{label}</span>
}
