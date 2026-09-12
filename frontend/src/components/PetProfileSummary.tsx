const SEX_LABELS: Record<'male' | 'female', string> = { male: 'Macho', female: 'Hembra' }

interface PetProfileLike {
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
