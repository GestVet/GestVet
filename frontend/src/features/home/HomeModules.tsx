import Icon from '../../components/Icon'
import type { IconName } from '../../components/icons'

interface Modulo {
  readonly icon: IconName
  readonly title: string
  readonly description: string
}

const MODULOS: readonly Modulo[] = [
  {
    icon: 'indicadores',
    title: 'Informes y análisis',
    description:
      'Indicadores de inasistencia, pagos atípicos y veterinarios a observar.',
  },
  {
    icon: 'cita',
    title: 'Gestión de citas',
    description: 'La agenda muestra solo lo que el veterinario publicó y todavía está libre.',
  },
  {
    icon: 'salud',
    title: 'Métricas de salud',
    description: 'Recordatorios de cuidado para no perder el seguimiento de cada mascota.',
  },
  {
    icon: 'carpeta',
    title: 'Historias clínicas',
    description: 'Registro clínico con adjuntos y exportación a PDF.',
  },
]

/**
 * Lo que ofrece el sistema: el titulo a la izquierda y los modulos en una
 * rejilla de dos columnas separada por filetes, en vez de cuatro tarjetas
 * iguales.
 */
export default function HomeModules() {
  return (
    <section
      aria-labelledby="oferta-titulo"
      className="grid scroll-mt-24 gap-8 lg:grid-cols-[1fr_2fr] lg:gap-16"
      id="oferta"
    >
      <div className="flex flex-col gap-3 lg:pt-7">
        <h2
          className="m-0 font-heading text-3xl leading-tight font-bold tracking-tight text-balance text-foreground"
          id="oferta-titulo"
        >
          El día a día de la clínica, en un solo sistema
        </h2>
        <p className="m-0 max-w-prose text-base leading-relaxed text-muted-foreground">
          El personal y los dueños de mascotas trabajan sobre la misma información.
        </p>
      </div>
      <ul className="m-0 grid list-none gap-x-10 p-0 sm:grid-cols-2">
        {MODULOS.map((modulo) => (
          <li key={modulo.title} className="flex gap-4 border-t border-border py-7">
            <span className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-secondary text-primary">
              <Icon name={modulo.icon} size={22} />
            </span>
            <div className="flex flex-col gap-1.5">
              <h3 className="m-0 font-heading text-base font-bold text-foreground">
                {modulo.title}
              </h3>
              <p className="m-0 text-sm leading-relaxed text-muted-foreground">
                {modulo.description}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
