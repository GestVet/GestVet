import { Fragment, useState } from 'react'

import AttachmentsPanel from './AttachmentsPanel'

const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

interface AttachmentLike {
  readonly id: number
  readonly filename: string
  readonly url: string
}

interface ClinicalEntryLike {
  readonly id: number
  readonly occurred_at: string
  readonly kind_label: string
  readonly diagnosis: string
  readonly treatment: string
  readonly weight_kg: string | null
  readonly notes: string
  readonly attachments: readonly AttachmentLike[]
}

interface ClinicalEntryRowProps {
  readonly entrada: ClinicalEntryLike
  readonly petId: number
  readonly canManageAttachments: boolean
}

export default function ClinicalEntryRow({
  entrada,
  petId,
  canManageAttachments,
}: ClinicalEntryRowProps) {
  const [expandido, setExpandido] = useState(false)

  return (
    <Fragment>
      <tr>
        <td>{FORMATO.format(new Date(entrada.occurred_at))}</td>
        <td>{entrada.kind_label}</td>
        <td>{entrada.diagnosis || '—'}</td>
        <td>{entrada.treatment || '—'}</td>
        <td>{entrada.weight_kg ? `${entrada.weight_kg} kg` : '—'}</td>
        <td>{entrada.notes}</td>
        <td>
          <button
            type="button"
            className="btn btn-plain"
            onClick={() => {
              setExpandido(!expandido)
            }}
          >
            {expandido
              ? 'Ocultar adjuntos'
              : `Ver adjuntos (${String(entrada.attachments.length)})`}
          </button>
        </td>
      </tr>
      {expandido ? (
        <tr>
          <td colSpan={7}>
            <AttachmentsPanel
              clinicalEntryId={entrada.id}
              petId={petId}
              attachments={entrada.attachments}
              canManage={canManageAttachments}
            />
          </td>
        </tr>
      ) : null}
    </Fragment>
  )
}
