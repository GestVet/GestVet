import { useMutation } from '@tanstack/react-query'

import { errorMessage } from '../services/api'
import { mostrarArchivo, reservarPestana } from '../services/descargas'

interface OpenArgs {
  readonly id: number
  readonly filename: string
  readonly pestana: Window | null
}

/**
 * Abre en otra pestaña un archivo que solo se entrega con la sesión.
 *
 * El token vive en el almacenamiento del navegador y un enlace común no lo
 * manda: el archivo se pide por el cliente HTTP y se muestra desde memoria.
 */
export function useFileOpener(fetchFile: (id: number) => Promise<Blob>) {
  const mutation = useMutation({
    mutationFn: async ({ id, filename, pestana }: OpenArgs) => {
      mostrarArchivo(await fetchFile(id), filename, pestana)
    },
    onError: (_error, { pestana }) => {
      pestana?.close()
    },
  })

  return {
    abrir: (id: number, filename: string) => {
      mutation.mutate({ id, filename, pestana: reservarPestana() })
    },
    isPending: mutation.isPending,
    isError: mutation.isError,
    errorMessage: mutation.isError
      ? errorMessage(mutation.error, 'No se pudo abrir el archivo.')
      : '',
  }
}
