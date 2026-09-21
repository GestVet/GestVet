import { useQuery } from '@tanstack/react-query'

import { fetchEvidenceFile } from '../../api/complaints'

function comoDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const lector = new FileReader()
    lector.onload = () => {
      resolve(typeof lector.result === 'string' ? lector.result : '')
    }
    lector.onerror = () => {
      reject(lector.error ?? new Error('No se pudo leer la imagen.'))
    }
    lector.readAsDataURL(blob)
  })
}

/**
 * La miniatura de una foto de evidencia, pedida con la sesión.
 *
 * Un `<img src>` no manda el token, así que la imagen se baja por el cliente
 * HTTP. Se guarda como `data:` y no como enlace de objeto: el caché de
 * consultas la suelta solo cuando nadie la muestra, sin un enlace que revocar.
 */
export function useEvidenceThumbnail(evidenceId: number, habilitada: boolean): string | null {
  const { data } = useQuery({
    queryKey: ['complaint-evidence-file', evidenceId],
    queryFn: async () => comoDataUrl(await fetchEvidenceFile(evidenceId)),
    enabled: habilitada,
    // El archivo de una evidencia no cambia nunca.
    staleTime: Infinity,
  })
  return data ?? null
}
