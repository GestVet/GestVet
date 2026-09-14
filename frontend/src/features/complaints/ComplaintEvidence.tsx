import Icon from '../../components/Icon'

interface ArchivoDeEvidencia {
  readonly id: number
  readonly filename: string
  readonly content_type: string
  readonly url: string
}

interface ComplaintEvidenceProps {
  readonly archivos: readonly ArchivoDeEvidencia[]
}

/** La evidencia de un reclamo: las fotos en miniatura, el resto como archivo. */
export default function ComplaintEvidence({ archivos }: ComplaintEvidenceProps) {
  return (
    <div className="flex flex-col gap-2">
      <p className="m-0 text-sm font-medium">Evidencia</p>
      {archivos.length === 0 ? (
        <p className="m-0 text-sm text-muted-foreground">Sin evidencia adjunta.</p>
      ) : (
        <ul className="m-0 flex list-none flex-wrap gap-3 p-0">
          {archivos.map((archivo) => (
            <li key={archivo.id}>
              <a
                href={archivo.url}
                target="_blank"
                rel="noreferrer"
                className="flex w-28 flex-col gap-1 rounded-md text-xs text-primary outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                {archivo.content_type.startsWith('image/') ? (
                  <img
                    src={archivo.url}
                    alt=""
                    loading="lazy"
                    className="size-28 rounded-md object-cover ring-1 ring-foreground/10"
                  />
                ) : (
                  <span className="flex size-28 items-center justify-center rounded-md bg-muted text-muted-foreground">
                    <Icon name="carpeta" size={28} />
                  </span>
                )}
                <span className="truncate underline underline-offset-4">{archivo.filename}</span>
                <span className="sr-only">(se abre en otra pestaña)</span>
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
