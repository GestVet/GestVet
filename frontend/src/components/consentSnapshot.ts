import type { ConsentTextContent } from './ConsentText'
import type { StatusTone } from './StatusBadge'

/** Lo que hace falta de un consentimiento para mostrarlo; coincide con la respuesta de la API. */
export interface ConsentLike {
  readonly kind_label: string
  readonly status: 'pending' | 'accepted' | 'declined' | 'expired' | 'waived_emergency'
  readonly status_label: string
  readonly pet_name: string | null
  readonly text_snapshot: string
  readonly signer_name: string | null
  readonly decided_at: string | null
  readonly channel_label: string | null
  readonly witness_name: string | null
  readonly decision_reason: string | null
  readonly created_at: string
  readonly details?: { readonly procedure?: string | null } | null
}

const FECHA_Y_HORA = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

export function formatConsentDate(iso: string): string {
  return FECHA_Y_HORA.format(new Date(iso))
}

/**
 * El texto copiado en el consentimiento, separado en título y cuerpo.
 *
 * El servidor lo arma como `título`, línea en blanco y `cuerpo` (con el
 * detalle del veterinario al final), así que el primer corte doble separa
 * los dos sin perder nada de lo que se firmó.
 */
export function signedContent(
  consent: Pick<ConsentLike, 'text_snapshot' | 'kind_label'>,
): ConsentTextContent {
  const texto = consent.text_snapshot
  const corte = texto.indexOf('\n\n')
  if (corte < 0) {
    return { title: consent.kind_label, body: texto }
  }
  return { title: texto.slice(0, corte), body: texto.slice(corte + 2) }
}

const TONO_POR_ESTADO: Readonly<Record<ConsentLike['status'], StatusTone | undefined>> = {
  pending: 'pending',
  accepted: 'completed',
  declined: 'cancelled',
  expired: undefined,
  waived_emergency: 'confirmed',
}

export function consentTone(status: ConsentLike['status']): StatusTone | undefined {
  return TONO_POR_ESTADO[status]
}

/** Quién respondió, cuándo y por qué vía, en una línea. */
export function consentDecisionLine(consent: ConsentLike): string {
  const partes: string[] = []
  if (consent.signer_name !== null) {
    partes.push(`Firmó ${consent.signer_name}`)
  }
  if (consent.decided_at !== null) {
    partes.push(formatConsentDate(consent.decided_at))
  }
  if (consent.channel_label !== null) {
    partes.push(consent.channel_label)
  }
  if (consent.witness_name !== null) {
    partes.push(`testigo: ${consent.witness_name}`)
  }
  if (partes.length === 0) {
    return `Pedido el ${formatConsentDate(consent.created_at)}`
  }
  return partes.join(' · ')
}
