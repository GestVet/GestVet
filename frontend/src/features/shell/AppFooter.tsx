import { Link } from 'react-router'

import Icon from '../../components/Icon'

interface AppFooterProps {
  /** Sin sesion se ofrecen los accesos; con sesion, el panel y el perfil. */
  readonly invitados: boolean
}

const ANIO = new Date().getFullYear()

const DIRECCION = 'Av. Prof. César Vallejo 95, Víctor Larco Herrera, Trujillo'

const MAPA = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(DIRECCION)}`

const ENLACES_INVITADO = [
  { to: '/#oferta', label: 'Qué ofrece' },
  { to: '/acceso', label: 'Iniciar sesión' },
  { to: '/registro', label: 'Crear una cuenta' },
] as const

const ENLACES_SESION = [
  { to: '/panel', label: 'Panel' },
  { to: '/perfil', label: 'Mi perfil' },
] as const

const ENLACE =
  'rounded-sm font-medium no-underline outline-none focus-visible:ring-3 focus-visible:ring-ring/50'

/**
 * El pie de todas las pantallas: la clinica, donde queda y los enlaces.
 *
 * Solo muestra datos que existen. El telefono, el correo, el RUC y el libro de
 * reclamaciones se agregan cuando haya una clinica real que los aporte.
 */
export default function AppFooter({ invitados }: AppFooterProps) {
  const enlaces = invitados ? ENLACES_INVITADO : ENLACES_SESION

  return (
    <footer className="border-t text-sm text-muted-foreground" id="contacto">
      <div className="mx-auto flex max-w-[1100px] flex-col gap-5 px-4 py-6 sm:px-6 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-col gap-1.5">
          <span className="flex items-center gap-2 font-heading font-semibold text-foreground">
            <Icon className="text-primary" name="huella" size={18} />
            GestVet · Clínica veterinaria en Trujillo
          </span>
          <address className="flex items-center gap-1.5 not-italic">
            <Icon className="shrink-0" name="ubicacion" size={15} />
            {DIRECCION}
          </address>
          <p className="m-0 flex items-center gap-1.5">
            <Icon className="shrink-0" name="horario" size={15} />
            Las 24 horas del día
          </p>
        </div>
        <nav aria-label="Enlaces del pie de página">
          <ul className="m-0 flex list-none flex-wrap gap-x-5 gap-y-2 p-0">
            {enlaces.map((enlace) => (
              <li key={enlace.label}>
                <Link className={`${ENLACE} text-foreground hover:text-primary`} to={enlace.to}>
                  {enlace.label}
                </Link>
              </li>
            ))}
            <li>
              <a
                className={`${ENLACE} text-primary underline-offset-4 hover:underline`}
                href={MAPA}
                rel="noreferrer"
                target="_blank"
              >
                Cómo llegar<span className="sr-only"> (se abre en otra pestaña)</span>
              </a>
            </li>
          </ul>
        </nav>
        <p className="m-0">© {ANIO} GestVet</p>
      </div>
    </footer>
  )
}
