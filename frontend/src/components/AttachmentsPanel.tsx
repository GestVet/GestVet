import { useRef } from 'react'

import { useAttachmentDelete, useAttachmentUpload } from '../hooks/useAttachments'
import FormMessage from './FormMessage'
import Icon from './Icon'
import { Button } from './ui/button'

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
 *
 * El selector de archivos se abre con un botón de verdad. Antes era una
 * etiqueta con aspecto de botón, y con el teclado no se podía alcanzar.
 */
export default function AttachmentsPanel({
  clinicalEntryId,
  petId,
  attachments,
  canManage,
}: AttachmentsPanelProps) {
  const subir = useAttachmentUpload(petId)
  const borrar = useAttachmentDelete(petId)
  const selector = useRef<HTMLInputElement>(null)

  return (
    <div className="flex flex-col gap-3">
      {attachments.length === 0 ? (
        <p className="m-0 text-sm text-muted-foreground">Todavía no hay adjuntos.</p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-2 p-0">
          {attachments.map((adjunto) => (
            <li key={adjunto.id} className="flex flex-wrap items-center justify-between gap-2">
              <a
                href={adjunto.url}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-primary underline underline-offset-4"
              >
                {adjunto.filename}
              </a>
              {canManage ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={borrar.isPending}
                  onClick={() => {
                    borrar.mutate(adjunto.id)
                  }}
                >
                  Quitar
                </Button>
              ) : null}
            </li>
          ))}
        </ul>
      )}

      {subir.isError ? <FormMessage tone="error">{subir.errorMessage}</FormMessage> : null}
      {borrar.isError ? <FormMessage tone="error">{borrar.errorMessage}</FormMessage> : null}

      {canManage ? (
        <>
          <Button
            type="button"
            variant="outline"
            className="self-start"
            disabled={subir.isPending}
            onClick={() => {
              selector.current?.click()
            }}
          >
            <Icon name="agregar" size={16} />
            <span>{subir.isPending ? 'Subiendo…' : 'Adjuntar archivo'}</span>
          </Button>
          <input
            ref={selector}
            type="file"
            accept={TIPOS_ACEPTADOS}
            hidden
            onChange={(evento) => {
              const archivo = evento.target.files?.[0]
              evento.target.value = ''
              if (archivo) {
                subir.mutate({ clinicalEntryId, file: archivo })
              }
            }}
          />
        </>
      ) : null}
    </div>
  )
}
