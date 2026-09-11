import { z } from 'zod'

/**
 * Forma del formulario de reserva. La comparten el formulario y sus campos.
 *
 * Los identificadores se validan como texto y no con `z.coerce.number()`: la
 * coercion hace que el tipo de entrada del formulario y el de salida difieran,
 * y react-hook-form deja de cuadrar. Un `<select>` devuelve texto; convertirlo
 * es trabajo del envio, que es donde se arma el cuerpo de la peticion.
 */
export const bookingSchema = z.object({
  pet_id: z.string().min(1, 'Elegí una mascota'),
  veterinarian_id: z.string().min(1, 'Elegí un veterinario'),
  appointment_type_id: z.string().min(1, 'Elegí el motivo'),
  scheduled_at: z.string().min(1, 'Elegí fecha y hora'),
  description: z.string().max(500).optional(),
})

export type BookingForm = z.infer<typeof bookingSchema>
