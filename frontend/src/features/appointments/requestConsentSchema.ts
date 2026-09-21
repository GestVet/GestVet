import { z } from 'zod'

import type { ConsentKind, RequestConsentRequest } from '../../api/types'
import { decimalParaApi, decimalRule, textoOpcional } from '../../components/formRules'

// Los mismos topes que el servidor.
const MAX_PROCEDIMIENTO = 200
const MAX_PRONOSTICO = 500
const MAX_NOTAS = 1000
const MAX_COSTO = 1_000_000

export type RequestableKind = Exclude<ConsentKind, 'emergency_risk'>

interface KindInfo {
  readonly value: RequestableKind
  readonly label: string
  /** Cómo se llama el campo de procedimiento para este tipo. */
  readonly procedureLabel: string
  /** Si el servidor lo exige: nadie autoriza "una cirugía" sin saber cuál. */
  readonly procedureRequired: boolean
}

export const REQUESTABLE_KINDS: readonly KindInfo[] = [
  {
    value: 'procedure',
    label: 'Cirugía o procedimiento invasivo',
    procedureLabel: 'Procedimiento',
    procedureRequired: true,
  },
  {
    value: 'anesthesia',
    label: 'Anestesia o sedación',
    procedureLabel: 'Procedimiento que requiere la anestesia',
    procedureRequired: true,
  },
  {
    value: 'hospitalization',
    label: 'Internación',
    procedureLabel: 'Motivo de la internación (opcional)',
    procedureRequired: false,
  },
  {
    value: 'high_risk',
    label: 'Pronóstico reservado y riesgo alto',
    procedureLabel: 'Diagnóstico o tratamiento propuesto (opcional)',
    procedureRequired: false,
  },
  {
    value: 'euthanasia',
    label: 'Eutanasia',
    procedureLabel: 'Motivo de la eutanasia',
    procedureRequired: true,
  },
]

export function kindInfo(kind: string): KindInfo | undefined {
  return REQUESTABLE_KINDS.find((info) => info.value === kind)
}

export const requestConsentSchema = z
  .object({
    kind: z.string().min(1, 'Elige qué consentimiento pedir'),
    procedure: textoOpcional(MAX_PROCEDIMIENTO),
    prognosis: textoOpcional(MAX_PRONOSTICO),
    estimated_cost: decimalRule({ max: MAX_COSTO, decimales: 2, unidad: 'soles' }),
    notes: textoOpcional(MAX_NOTAS),
  })
  .refine((valores) => !kindInfo(valores.kind)?.procedureRequired || valores.procedure !== '', {
    path: ['procedure'],
    message: 'Indica el procedimiento: el responsable tiene que saber qué autoriza',
  })

export type RequestConsentInput = z.input<typeof requestConsentSchema>
export type RequestConsentValues = z.output<typeof requestConsentSchema>

export function emptyRequest(kind: RequestableKind | ''): RequestConsentInput {
  return { kind, procedure: '', prognosis: '', estimated_cost: '', notes: '' }
}

export function toRequestPayload(
  appointmentId: number,
  valores: RequestConsentValues,
): RequestConsentRequest {
  return {
    appointment_id: appointmentId,
    kind: valores.kind as RequestableKind,
    details: {
      procedure: valores.procedure || null,
      prognosis: valores.prognosis || null,
      estimated_cost: decimalParaApi(valores.estimated_cost),
      notes: valores.notes || null,
    },
  }
}
