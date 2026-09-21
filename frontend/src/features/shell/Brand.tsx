import { Link } from 'react-router'

import GestVetMark from './GestVetMark'

interface BrandProps {
  readonly to: string
}

export default function Brand({ to }: BrandProps) {
  return (
    <Link
      to={to}
      aria-label="GestVet, ir al inicio"
      className="inline-flex items-center gap-2.5 rounded-lg font-heading text-xl font-bold text-foreground outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
    >
      <GestVetMark size={34} />
      <span aria-hidden="true" className="flex items-center tracking-tight text-xl font-black">
        <span className="text-foreground">Gest</span>
        <span className="text-primary">Vet</span>
      </span>
    </Link>
  )
}

