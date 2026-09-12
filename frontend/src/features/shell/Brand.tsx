import { Link } from 'react-router'

import Icon from '../../components/Icon'

interface BrandProps {
  readonly to: string
}

export default function Brand({ to }: BrandProps) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-2 rounded-lg font-heading text-xl font-bold text-primary outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
    >
      <Icon name="huella" size={28} />
      <span>GestVet</span>
    </Link>
  )
}
