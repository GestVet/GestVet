import type { ReactNode } from 'react'

import MicrochipLookup from './MicrochipLookup'

const SEX_LABELS: Record<'male' | 'female', string> = { male: 'Macho', female: 'Hembra' }
// La fecha de nacimiento es un día, no un instante: se muestra en UTC para que
// en Perú (UTC-5) no retroceda al día anterior.
const FORMATO_FECHA = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeZone: 'UTC' })

interface PetProfileLike {
  readonly breed: string
  readonly birth_date: string
  readonly sex: 'male' | 'female' | null
  readonly color: string
  readonly microchip_number: string
  readonly temperament: string
  readonly weight_kg: string | null
  readonly height_cm: string | null
  readonly is_sterilized: boolean | null
  readonly allergies: string
}

interface PetProfileSummaryProps {
  readonly mascota: PetProfileLike
}

function esterilizadoLabel(valor: boolean | null): string {
  if (valor === null) return 'No evaluado'
  return valor ? 'Sí' : 'No'
}

/**
 * Ficha completa de la mascota, siempre en modo lectura.
 *
 * Son pares de dato y valor, no una tabla: una lista de definicion lo dice
 * asi al lector de pantalla y en el celular no necesita desplazarse.
 */
export default function PetProfileSummary({ mascota }: PetProfileSummaryProps) {
  const filas: readonly [string, ReactNode][] = [
    ['Raza', mascota.breed],
    ['Fecha de nacimiento', FORMATO_FECHA.format(new Date(mascota.birth_date))],
    ['Sexo', mascota.sex ? SEX_LABELS[mascota.sex] : 'No especificado'],
    ['Color', mascota.color || '—'],
    [
      'Microchip',
      mascota.microchip_number ? <MicrochipLookup numero={mascota.microchip_number} /> : '—',
    ],
    ['Temperamento', mascota.temperament || '—'],
    ['Peso', mascota.weight_kg ? `${mascota.weight_kg} kg` : '—'],
    ['Altura', mascota.height_cm ? `${mascota.height_cm} cm` : '—'],
    ['Esterilizado', esterilizadoLabel(mascota.is_sterilized)],
    ['Alergias', mascota.allergies || '—'],
  ]

  return (
    <dl className="m-0 grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
      {filas.map(([campo, valor]) => (
        <div key={campo} className="flex flex-col gap-0.5">
          <dt className="text-muted-foreground">{campo}</dt>
          <dd className="m-0 font-medium">{valor}</dd>
        </div>
      ))}
    </dl>
  )
}
