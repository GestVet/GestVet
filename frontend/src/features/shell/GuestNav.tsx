import { Link } from 'react-router'

interface GuestNavProps {
  readonly className?: string
}

const ENLACES = [
  { to: '/', hash: '', label: 'Inicio' },
  { to: '/', hash: 'oferta', label: 'Qué ofrece' },
  { to: '/', hash: 'contacto', label: 'Contacto' },
] as const

export default function GuestNav({ className }: GuestNavProps) {
  return (
    <nav aria-label="Secciones de la página" className={className}>
      <ul className="m-0 flex list-none flex-wrap items-center justify-center gap-1 p-0 sm:gap-2">
        {ENLACES.map((enlace) => (
          <li key={enlace.label}>
            <Link
              className="inline-flex rounded-lg px-2.5 py-1.5 text-sm font-medium text-foreground no-underline outline-none hover:bg-muted focus-visible:ring-3 focus-visible:ring-ring/50"
              to={{
                pathname: enlace.to,
                hash: enlace.hash === '' ? '' : `#${enlace.hash}`,
              }}
            >
              {enlace.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}
