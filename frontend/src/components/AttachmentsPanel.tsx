import { useAttachmentDelete, useAttachmentUpload } from '../hooks/useAttachments'
import FormMessage from './FormMessage'
import Icon from './Icon'

const TIPOS_ACEPTADOS = 'image/jpeg,image/png,image/webp,application/pdf'

interface AttachmentLike {
  readonly id: number
  readonly filename: string
  readonly url: string
}

interface AttachmentsPanelProps {
  readonly clinicalEntryId: number
  readonly petId: number
  readonly attachments: readonly AttachmentLike[]
  readonly canManage: boolean
}

/**
 * Lista y gestiona los adjuntos de una entrada de la historia clínica.
 *
 * Puramente presentacional salvo por las mutaciones, que llegan ya resueltas
 * desde `hooks/useAttachments`: así lo pueden usar tanto la vista del cliente
 * (`canManage=false`, solo lectura) como la del personal, sin que ninguna
 * importe a la otra.
 */
export default function AttachmentsPanel({
  clinicalEntryId,
  petId,
  attachments,
  canManage,
}: AttachmentsPanelProps) {
  const subir = useAttachmentUpload(petId)
  const borrar = useAttachmentDelete(petId)

  return (
    <div className="stack">
      {attachments.length === 0 ? (
        <p className="empty">Todavía no hay adjuntos.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Archivo</th>
              {canManage ? <th>Acciones</th> : null}
            </tr>
          </thead>
          <tbody>
            {attachments.map((adjunto) => (
              <tr key={adjunto.id}>
                <td>
                  <a href={adjunto.url} target="_blank" rel="noreferrer">
                    {adjunto.filename}
                  </a>
                </td>
                {canManage ? (
                  <td>
                    <button
                      type="button"
                      className="btn btn-plain"
                      disabled={borrar.isPending}
                      onClick={() => {
                        borrar.mutate(adjunto.id)
                      }}
                    >
                      Quitar
                    </button>
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {subir.isError ? <FormMessage tone="error">{subir.errorMessage}</FormMessage> : null}
      {borrar.isError ? <FormMessage tone="error">{borrar.errorMessage}</FormMessage> : null}

      {canManage ? (
        <label className="btn btn-plain" style={{ width: 'fit-content' }}>
          <Icon name="agregar" size={16} />
          <span>{subir.isPending ? 'Subiendo…' : 'Adjuntar archivo'}</span>
          <input
            type="file"
            accept={TIPOS_ACEPTADOS}
            hidden
            disabled={subir.isPending}
            onChange={(evento) => {
              const archivo = evento.target.files?.[0]
              evento.target.value = ''
              if (archivo) {
                subir.mutate({ clinicalEntryId, file: archivo })
              }
            }}
          />
        </label>
      ) : null}
    </div>
  )
}
