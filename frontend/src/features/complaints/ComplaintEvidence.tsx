import { fetchEvidenceFile } from '../../api/complaints'
import FormMessage from '../../components/FormMessage'
import { useFileOpener } from '../../hooks/useFileOpener'
import EvidenceItem from './EvidenceItem'

interface ArchivoDeEvidencia {
  readonly id: number
  readonly filename: string
  readonly content_type: string
}

interface ComplaintEvidenceProps {
  readonly archivos: readonly ArchivoDeEvidencia[]
}

/** La evidencia de un reclamo: las fotos en miniatura, el resto como archivo. */
export default function ComplaintEvidence({ archivos }: ComplaintEvidenceProps) {
  const abrir = useFileOpener(fetchEvidenceFile)

  return (
    <div className="flex flex-col gap-2">
      <p className="m-0 text-sm font-medium">Evidencia</p>
      {archivos.length === 0 ? (
        <p className="m-0 text-sm text-muted-foreground">Sin evidencia adjunta.</p>
      ) : (
        <ul className="m-0 flex list-none flex-wrap gap-3 p-0">
          {archivos.map((archivo) => (
            <li key={archivo.id}>
              <EvidenceItem
                id={archivo.id}
                filename={archivo.filename}
                contentType={archivo.content_type}
                onOpen={abrir.abrir}
              />
            </li>
          ))}
        </ul>
      )}
      {abrir.isError ? <FormMessage tone="error">{abrir.errorMessage}</FormMessage> : null}
    </div>
  )
}
