const SEX_LABELS: Record<'male' | 'female', string> = { male: 'Macho', female: 'Hembra' }
const FORMATO_FECHA = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium' })

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

/** Ficha completa de la mascota, siempre en modo lectura. */
export default function PetProfileSummary({ mascota }: PetProfileSummaryProps) {
  const filas: readonly [string, string][] = [
    ['Raza', mascota.breed],
    ['Fecha de nacimiento', FORMATO_FECHA.format(new Date(mascota.birth_date))],
    ['Sexo', mascota.sex ? SEX_LABELS[mascota.sex] : 'No especificado'],
    ['Color', mascota.color || '—'],
    ['Microchip', mascota.microchip_number || '—'],
    ['Temperamento', mascota.temperament || '—'],
    ['Peso', mascota.weight_kg ? `${mascota.weight_kg} kg` : '—'],
    ['Altura', mascota.height_cm ? `${mascota.height_cm} cm` : '—'],
    ['Esterilizado', esterilizadoLabel(mascota.is_sterilized)],
    ['Alergias', mascota.allergies || '—'],
  ]

  return (
    <table>
      <tbody>
        {filas.map(([campo, valor]) => (
          <tr key={campo}>
            <th scope="row">{campo}</th>
            <td>{valor}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
