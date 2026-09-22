import type { SpecialtyResponse } from '../../api/types'

interface SpecialtyBadgesProps {
  readonly specialties: readonly SpecialtyResponse[]
}

export default function SpecialtyBadges({ specialties }: SpecialtyBadgesProps) {
  if (specialties.length === 0) {
    return <span className="text-sm text-muted-foreground">Sin especialidad</span>
  }
  return (
    <ul className="m-0 flex list-none flex-wrap gap-1 p-0">
      {specialties.map((especialidad) => (
        <li
          key={especialidad.id}
          className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
        >
          {especialidad.name}
        </li>
      ))}
    </ul>
  )
}
