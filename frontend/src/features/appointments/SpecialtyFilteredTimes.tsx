import { useState } from 'react'

import { Button } from '../../components/ui/button'
import VeterinarianTimes, { type OfertaDeVeterinario } from './VeterinarianTimes'

interface SpecialtyFilteredTimesProps {
  readonly ofertas: readonly OfertaDeVeterinario[]
  /** Con qué filtrar; `null` cuando no se marcó ninguna y se muestra a todos. */
  readonly specialtyId: number | null
  readonly dia: string
  readonly durationMinutes: number
  readonly veterinarianId: number
  readonly scheduledAt: string
  readonly onSelect: (veterinarianId: number, time: string) => void
}

function conEspecialidad(
  ofertas: readonly OfertaDeVeterinario[],
  specialtyId: number,
): OfertaDeVeterinario[] {
  return ofertas.filter((oferta) =>
    oferta.especialidades.some((especialidad) => especialidad.id === specialtyId),
  )
}

/**
 * Filtra la lista de veterinarios por especialidad, con salida a "ver todos".
 *
 * Un componente aparte y no un `if` en `BookingSlotPicker`: así su estado de
 * "ver todos" nace en `false` con solo montarlo de nuevo (la clave del padre
 * es la especialidad elegida) y no hace falta un efecto para reiniciarlo.
 */
export default function SpecialtyFilteredTimes({
  ofertas,
  specialtyId,
  ...resto
}: SpecialtyFilteredTimesProps) {
  const [verTodos, setVerTodos] = useState(false)
  const filtradas = specialtyId === null ? ofertas : conEspecialidad(ofertas, specialtyId)
  const sinNadie = specialtyId !== null && filtradas.length === 0
  const ofertasAMostrar = verTodos || sinNadie ? ofertas : filtradas

  if (specialtyId === null) {
    return <VeterinarianTimes ofertas={ofertas} {...resto} />
  }

  return (
    <>
      {sinNadie ? (
        <p className="m-0 rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground">
          Nadie con esa especialidad tiene hora libre este día. Se muestra a todo el equipo
          disponible; elegir a alguien sin esa especialidad es tu decisión.
        </p>
      ) : null}
      {!sinNadie && !verTodos ? (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="self-start"
          onClick={() => {
            setVerTodos(true)
          }}
        >
          Ver todos los veterinarios disponibles
        </Button>
      ) : null}
      <VeterinarianTimes ofertas={ofertasAMostrar} {...resto} />
    </>
  )
}
