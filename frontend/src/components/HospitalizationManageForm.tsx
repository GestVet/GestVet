import { useState } from 'react'

import { useAddHospitalizationNote, useDischargeHospitalization } from '../hooks/useHospitalizations'
import FormMessage from './FormMessage'

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

  return (
    <div className="stack">
      <div className="field">
        <label htmlFor={`nota-${String(hospitalizationId)}`}>Nota de seguimiento</label>
        <textarea
          id={`nota-${String(hospitalizationId)}`}
          rows={2}
          value={nota}
          onChange={(evento) => {
            setNota(evento.target.value)
          }}
        />
      </div>
      {agregarNota.isError ? (
        <FormMessage tone="error">{agregarNota.errorMessage}</FormMessage>
      ) : null}
      <button
        type="button"
        className="btn btn-plain"
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
      </button>

      <div className="field">
        <label htmlFor={`alta-${String(hospitalizationId)}`}>Notas de alta (opcional)</label>
        <textarea
          id={`alta-${String(hospitalizationId)}`}
          rows={2}
          value={notasDeAlta}
          onChange={(evento) => {
            setNotasDeAlta(evento.target.value)
          }}
        />
      </div>
      {darDeAlta.isError ? <FormMessage tone="error">{darDeAlta.errorMessage}</FormMessage> : null}
      <button
        type="button"
        className="btn btn-green"
        disabled={darDeAlta.isPending}
        onClick={() => {
          darDeAlta.mutate({ hospitalizationId, dischargeNotes: notasDeAlta })
        }}
      >
        {darDeAlta.isPending ? 'Dando de alta…' : 'Dar de alta'}
      </button>
    </div>
  )
}
