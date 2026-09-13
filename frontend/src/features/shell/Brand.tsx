import { Link } from 'react-router'

import GestVetMark from './GestVetMark'

interface BrandProps {
  readonly to: string
}

export default function Brand({ to }: BrandProps) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-2 rounded-lg font-heading text-xl font-bold text-foreground outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
    >
      <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-secondary/60">
        <GestVetMark size={26} />
      </span>
      <span>GestVet</span>
    </Link>
  )
}
