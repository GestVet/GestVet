import { Link } from 'react-router'

import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'

/**
 * La oferta del heroe. Los dos datos del pie repiten lo que la clinica ya
 * publica: el horario aprobado y el distrito de la direccion.
 */
export default function HomeHeroCopy() {
  return (
    <div className="flex flex-col gap-7">
      <div className="flex flex-col gap-4">
        <h1 className="m-0 font-heading text-[clamp(2.25rem,3.8vw,3rem)] leading-[1.1] font-bold tracking-tight text-balance text-foreground">
          GestVet: la gestión veterinaria simplificada
        </h1>
        <p className="m-0 text-lg font-semibold text-primary">
          Clínica veterinaria en Trujillo
        </p>
      </div>
      <p className="m-0 max-w-prose text-base leading-relaxed text-muted-foreground">
        Como clínica líder en la ciudad, ampliamos nuestros servicios para darte la
        seguridad y el cuidado que tu mascota merece. Atendemos las 24 horas del día.
      </p>
      <div className="flex flex-wrap gap-3">
        <Button asChild size="lg" className="h-11 px-6">
          <Link to="/registro">Crear una cuenta</Link>
        </Button>
        <Button asChild size="lg" variant="outline" className="h-11 px-6">
          <Link to="/acceso">Iniciar sesión</Link>
        </Button>
      </div>
      <ul className="m-0 flex list-none flex-wrap gap-x-6 gap-y-3 border-t border-border p-0 pt-5 text-sm text-foreground">
        <li className="flex items-center gap-2">
          <Icon className="text-primary" name="horario" size={18} />
          Las 24 horas del día
        </li>
        <li className="flex items-center gap-2">
          <Icon className="text-primary" name="ubicacion" size={18} />
          Víctor Larco Herrera, Trujillo
        </li>
      </ul>
    </div>
  )
}
