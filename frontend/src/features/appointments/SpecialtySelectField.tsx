import { useQuery } from '@tanstack/react-query'
import type { UseFormRegister } from 'react-hook-form'

import { fetchSpecialties, specialtiesQueryKey } from '../../api/directory'
import SelectField from '../../components/SelectField'
import { NativeSelectOptGroup, NativeSelectOption } from '../../components/ui/native-select'
import type { BookingForm } from './bookingSchema'

interface SpecialtySelectFieldProps {
  readonly register: UseFormRegister<BookingForm>
  readonly onChange: () => void
}

/**
 * Con qué necesita atención la mascota, agrupado por categoría.
 *
 * Solo filtra con quién ofrecer la reserva: elegir a alguien sin esta
 * especialidad sigue siendo posible, y decisión de quien reserva.
 */
export default function SpecialtySelectField({ register, onChange }: SpecialtySelectFieldProps) {
  const especialidades = useQuery({ queryKey: specialtiesQueryKey, queryFn: fetchSpecialties })
  const categorias = [...new Set(especialidades.data?.items.map((item) => item.category) ?? [])]

  return (
    <SelectField
      id="specialty_id"
      label="¿Qué necesita tu mascota? (opcional)"
      icon="diagnostico"
      placeholder="Cualquier veterinario disponible"
      field={register('specialty_id', { onChange })}
      hint="Prioriza a quien tiene esa especialidad. Tú decides con quién reservar."
    >
      {categorias.map((categoria) => {
        const items = especialidades.data?.items.filter((item) => item.category === categoria)
        if (items === undefined || items.length === 0) {
          return null
        }
        return (
          <NativeSelectOptGroup key={categoria} label={items[0].category_label}>
            {items.map((item) => (
              <NativeSelectOption key={item.id} value={item.id}>
                {item.name}
              </NativeSelectOption>
            ))}
          </NativeSelectOptGroup>
        )
      })}
    </SelectField>
  )
}
