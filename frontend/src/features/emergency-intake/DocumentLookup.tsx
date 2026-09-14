import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import { lookUpDocument } from '../../api/directory'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { Checkbox } from '../../components/ui/checkbox'
import { Label } from '../../components/ui/label'
import { errorMessage } from '../../services/api'

const DNI_COMPLETO = /^\d{8}$/u

interface DocumentLookupProps {
  readonly documentId: string
  readonly onFound: (nombres: string, apellidos: string) => void
}

function estado(completo: boolean, encontrado: string | null): string {
  if (encontrado !== null) {
    return `Se completó con ${encontrado}. Revísalo antes de abrir la emergencia.`
  }
  return completo ? '' : 'Escribe los 8 dígitos del DNI para completar el nombre.'
}

/**
 * Completar nombre y apellido desde el DNI, con la autorización del cliente.
 *
 * Con apuro es fácil tipear mal un apellido. La consulta solo se habilita
 * cuando el cliente autorizó y el DNI está completo; cada una queda en
 * Movimientos. Si el servicio no está disponible, se sigue escribiendo a mano.
 */
export default function DocumentLookup({ documentId, onFound }: DocumentLookupProps) {
  const [autorizado, setAutorizado] = useState(false)
  const [encontrado, setEncontrado] = useState<string | null>(null)
  const consulta = useMutation({
    mutationFn: lookUpDocument,
    onSuccess: (persona) => {
      onFound(persona.first_names, persona.last_names)
      setEncontrado(`${persona.first_names} ${persona.last_names}`)
    },
  })
  const completo = DNI_COMPLETO.test(documentId)

  return (
    <div className="flex flex-col gap-3 rounded-lg border bg-muted/30 p-3 sm:col-span-2">
      <div className="flex items-start gap-2.5">
        <Checkbox
          id="dni-autorizado"
          checked={autorizado}
          onCheckedChange={(marcado) => {
            setAutorizado(marcado === true)
          }}
        />
        <Label htmlFor="dni-autorizado" className="leading-snug font-normal">
          El cliente autoriza consultar su DNI para completar su nombre.
        </Label>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={!autorizado || !completo || consulta.isPending}
          onClick={() => {
            setEncontrado(null)
            consulta.mutate(documentId)
          }}
        >
          <Icon name="buscar" size={14} />
          <span>{consulta.isPending ? 'Consultando…' : 'Completar con el DNI'}</span>
        </Button>
        <p className="m-0 text-sm text-muted-foreground" aria-live="polite">
          {estado(completo, encontrado)}
        </p>
      </div>
      {consulta.isError ? (
        <FormMessage tone="error">
          {errorMessage(consulta.error, 'No se pudo consultar el DNI. Escribe el nombre a mano.')}
        </FormMessage>
      ) : null}
    </div>
  )
}
