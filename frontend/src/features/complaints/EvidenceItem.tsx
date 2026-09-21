import Icon from '../../components/Icon'
import { useEvidenceThumbnail } from './useEvidenceThumbnail'

interface EvidenceItemProps {
  readonly id: number
  readonly filename: string
  readonly contentType: string
  readonly onOpen: (id: number, filename: string) => void
}

/** Un archivo de evidencia: la foto en miniatura, el resto con un icono. */
export default function EvidenceItem({ id, filename, contentType, onOpen }: EvidenceItemProps) {
  const esImagen = contentType.startsWith('image/')
  const miniatura = useEvidenceThumbnail(id, esImagen)

  return (
    <button
      type="button"
      className="flex w-28 cursor-pointer flex-col gap-1 rounded-md text-left text-xs text-primary outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
      onClick={() => {
        onOpen(id, filename)
      }}
    >
      {miniatura === null ? (
        <span className="flex size-28 items-center justify-center rounded-md bg-muted text-muted-foreground">
          <Icon name="carpeta" size={28} />
        </span>
      ) : (
        <img
          src={miniatura}
          alt=""
          className="size-28 rounded-md object-cover ring-1 ring-foreground/10"
        />
      )}
      <span className="truncate underline underline-offset-4">{filename}</span>
      <span className="sr-only">(se abre en otra pestaña)</span>
    </button>
  )
}
