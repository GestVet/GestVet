import type { ConsentResponse } from '../../api/types'
import type { RequestableKind } from './requestConsentSchema'

/** Qué ventana tiene abierta el panel de consentimientos, si alguna. */
export type ConsentDialog =
  | { readonly tipo: 'pedir' | 'eximir'; readonly kind: RequestableKind | '' }
  | { readonly tipo: 'firmar'; readonly consent: ConsentResponse }
