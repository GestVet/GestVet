import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'

import { fetchHealth, healthQueryKey } from '../../api/health'
import Icon from '../../components/Icon'
import type { IconName } from '../../components/icons'
import { Button } from '../../components/ui/button'
import { Card, CardContent } from '../../components/ui/card'
import SystemStatus from './SystemStatus'

interface Modulo {
  readonly icon: IconName
  readonly title: string
  readonly description: string
}

const MODULOS: readonly Modulo[] = [
  {
    icon: 'mascota',
    title: 'Tus mascotas',
    description: 'Registrá a cada una con su especie, su raza y su fecha de nacimiento.',
  },
  {
    icon: 'agenda',
    title: 'Citas con hora real',
    description: 'La agenda muestra solo lo que el veterinario publicó y todavía está libre.',
  },
  {
    icon: 'emergencia',
    title: 'Emergencias 24 horas',
    description: 'Se abre en el momento y el sistema asigna al veterinario de guardia.',
  },
]

export default function HomeView() {
  const health = useQuery({ queryKey: healthQueryKey, queryFn: fetchHealth })

  return (
    <div className="flex flex-col gap-6">
      <Card className="gap-0 py-0 shadow-sm">
        <CardContent className="grid items-center gap-8 p-6 sm:p-8 md:grid-cols-[1fr_18rem]">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1">
              <h1 className="m-0 font-heading text-3xl leading-tight font-bold text-primary sm:text-4xl">
                Bienvenido a GestVet
              </h1>
              <p className="m-0 text-base font-medium text-foreground">
                Clínica veterinaria en Trujillo
              </p>
            </div>
            <p className="m-0 max-w-prose text-base leading-relaxed text-muted-foreground">
              Como clínica líder en la ciudad, ampliamos nuestros servicios para darte la
              seguridad y el cuidado que tu mascota merece. Atendemos las 24 horas del día.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button asChild variant="success" size="lg" className="h-11 px-5">
                <Link to="/registro">
                  <Icon name="agregar" size={16} />
                  <span>Crear una cuenta</span>
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="h-11 px-5">
                <Link to="/acceso">Ya tengo cuenta</Link>
              </Button>
            </div>
          </div>

          <SystemStatus
            isPending={health.isPending}
            isError={health.isError}
            data={health.data}
          />
        </CardContent>
      </Card>

      <section aria-label="Qué ofrece el sistema" className="grid gap-4 md:grid-cols-3">
        {MODULOS.map((modulo) => (
          <Card key={modulo.title} className="gap-3 px-5 py-5 shadow-sm">
            <Icon className="text-primary" name={modulo.icon} size={28} />
            <h2 className="m-0 font-heading text-lg font-semibold text-primary">
              {modulo.title}
            </h2>
            <p className="m-0 text-sm leading-relaxed text-muted-foreground">
              {modulo.description}
            </p>
          </Card>
        ))}
      </section>
    </div>
  )
}
