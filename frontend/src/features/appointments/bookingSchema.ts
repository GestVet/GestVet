import { z } from 'zod'

import { textoOpcional } from '../../components/formRules'

/**
 * Forma del formulario de reserva. La comparten el formulario y sus campos.
 *
 * Los identificadores se validan como texto y no con `z.coerce.number()`: la
 * coercion hace que el tipo de entrada del formulario y el de salida difieran,
 * y react-hook-form deja de cuadrar. Un `<select>` devuelve texto; convertirlo
 * es trabajo del envio, que es donde se arma el cuerpo de la peticion.
 *
 * Veterinario y hora los fija el selector de horas en un solo gesto, asi que
 * comparten el mismo mensaje.
 */
export const bookingSchema = z.object({
  pet_id: z.string().min(1, 'Elige una mascota'),
  appointment_type_id: z.string().min(1, 'Elige el tipo de atención'),
  veterinarian_id: z.string().min(1, 'Elige un día y una hora'),
  scheduled_at: z.string().min(1, 'Elige un día y una hora'),
  description: textoOpcional(500),
})

export type BookingForm = z.infer<typeof bookingSchema>
