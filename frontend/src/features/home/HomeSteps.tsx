import { Link } from 'react-router'

import Icon from '../../components/Icon'
import type { IconName } from '../../components/icons'
import { Button } from '../../components/ui/button'

interface Paso {
  readonly icon: IconName
  readonly title: string
  readonly description: string
}

const PASOS: readonly Paso[] = [
  {
    icon: 'registrarse',
    title: 'Crea tu cuenta',
    description: 'Con tu nombre, tu correo y tu DNI.',
  },
  {
    icon: 'mascota',
    title: 'Registra a tu mascota',
    description: 'Sus datos quedan guardados para cada cita.',
  },
  {
    icon: 'cita',
    title: 'Elige un horario',
    description: 'Solo ves los horarios libres que publicó cada veterinario.',
  },
]

/**
 * Como reservar la primera cita.
 *
 * Es una secuencia de verdad, asi que va en una lista ordenada: el lector de
 * pantalla anuncia el orden y la vista lo muestra de izquierda a derecha. Es
 * el unico bloque azul de la portada, el lugar donde la persona decide
 * registrarse.
 */
export default function HomeSteps() {
  return (
    <section
      aria-labelledby="pasos-titulo"
      className="flex scroll-mt-24 flex-col gap-10 rounded-2xl bg-primary px-6 py-10 text-primary-foreground sm:px-10 sm:py-12"
      id="como-reservar"
    >
      <div className="flex flex-col gap-3">
        <h2
          className="m-0 font-heading text-3xl leading-tight font-bold tracking-tight text-balance"
          id="pasos-titulo"
        >
          Reserva tu primera cita
        </h2>
        <p className="m-0 max-w-prose text-base leading-relaxed text-primary-foreground/85">
          Todo se hace desde tu cuenta, sin llamar a la clínica.
        </p>
      </div>

      <ol className="m-0 grid list-none gap-8 p-0 md:grid-cols-3 md:gap-6">
        {PASOS.map((paso) => (
          <li key={paso.title} className="flex flex-col gap-4 border-t border-white/25 pt-6">
            <span className="flex size-11 items-center justify-center rounded-full bg-white text-primary">
              <Icon name={paso.icon} size={22} />
            </span>
            <div className="flex flex-col gap-1.5">
              <h3 className="m-0 font-heading text-lg font-bold">{paso.title}</h3>
              <p className="m-0 text-sm leading-relaxed text-primary-foreground/85">
                {paso.description}
              </p>
            </div>
          </li>
        ))}
      </ol>

      <div>
        <Button asChild size="lg" variant="secondary" className="h-11 px-6">
          <Link to="/registro">Crear una cuenta</Link>
        </Button>
      </div>
    </section>
  )
}
