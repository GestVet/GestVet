import { useState } from 'react'

import { useAddHospitalizationNote, useDischargeHospitalization } from '../hooks/useHospitalizations'
import FormMessage from './FormMessage'
import { Button } from './ui/button'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'

interface HospitalizationManageFormProps {
  readonly hospitalizationId: number
  readonly petId: number
}

/** Notas de seguimiento y alta de una internación abierta. Solo lo ve el personal. */
export default function HospitalizationManageForm({
  hospitalizationId,
  petId,
}: HospitalizationManageFormProps) {
  const [nota, setNota] = useState('')
  const [notasDeAlta, setNotasDeAlta] = useState('')
  const agregarNota = useAddHospitalizationNote(petId)
  const darDeAlta = useDischargeHospitalization(petId)
  const notaId = `nota-${String(hospitalizationId)}`
  const altaId = `alta-${String(hospitalizationId)}`

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="flex flex-col gap-2">
        <Label htmlFor={notaId}>Nota de seguimiento</Label>
        <Textarea
          id={notaId}
          rows={2}
          value={nota}
          onChange={(evento) => {
            setNota(evento.target.value)
          }}
        />
        {agregarNota.isError ? (
          <FormMessage tone="error">{agregarNota.errorMessage}</FormMessage>
        ) : null}
        <Button
          type="button"
          variant="outline"
          className="self-start"
          disabled={agregarNota.isPending || nota.trim() === ''}
          onClick={() => {
            agregarNota.mutate(
              { hospitalizationId, note: nota },
              {
                onSuccess: () => {
                  setNota('')
                },
              },
            )
          }}
        >
          {agregarNota.isPending ? 'Agregando…' : 'Agregar nota'}
        </Button>
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor={altaId}>Notas de alta (opcional)</Label>
        <Textarea
          id={altaId}
          rows={2}
          value={notasDeAlta}
          onChange={(evento) => {
            setNotasDeAlta(evento.target.value)
          }}
        />
        {darDeAlta.isError ? (
          <FormMessage tone="error">{darDeAlta.errorMessage}</FormMessage>
        ) : null}
        <Button
          type="button"
          variant="success"
          className="self-start"
          disabled={darDeAlta.isPending}
          onClick={() => {
            darDeAlta.mutate({ hospitalizationId, dischargeNotes: notasDeAlta })
          }}
        >
          {darDeAlta.isPending ? 'Dando de alta…' : 'Dar de alta'}
        </Button>
      </div>
    </div>
  )
}
