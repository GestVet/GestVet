import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { firmaRule, MAX_FIRMA } from '../services/fieldRules'

const esquema = z.object({
  accepted: z.boolean().refine((marcado) => marcado, 'Marca la casilla para aceptar'),
  signer_name: firmaRule,
})

export type ConsentSignInput = z.input<typeof esquema>
export type ConsentSignValues = z.output<typeof esquema>

/** El formulario de una firma: la casilla sin marcar y el nombre, con la regla del servidor. */
export function useConsentSignForm(defaultSignerName: string) {
  const form = useForm<ConsentSignInput, unknown, ConsentSignValues>({
    resolver: zodResolver(esquema),
    defaultValues: { accepted: false, signer_name: defaultSignerName },
  })
  return { form, maxSignerLength: MAX_FIRMA }
}
