import { zodResolver } from '@hookform/resolvers/zod'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'

import DialogFormActions from '../../components/DialogFormActions'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import type { IconName } from '../../components/icons'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import {
  buscarCoincidencias,
  formatearNombreDeCatalogo,
  type NombreDelCatalogo,
  problemaDelNombre,
} from '../../services/catalogName'
import SimilarNames from './SimilarNames'
import { useCatalogChange } from './useCatalogChange'

export interface CatalogEntryFormProps {
  readonly id: string
  readonly label: string
  readonly placeholder: string
  readonly icon: IconName
  readonly maxLength: number
  readonly submitLabel: string
  /** Al corregir, el nombre actual. Sin él, el formulario agrega uno nuevo. */
  readonly initialName?: string
  /** Lo ya cargado con qué compararlo, sin el nombre que se está corrigiendo. */
  readonly existing: readonly NombreDelCatalogo[]
  readonly onSave: (name: string) => Promise<unknown>
  /** Cierra la ventana: al cancelar o al guardar. */
  readonly onClose: () => void
}

interface Formulario {
  readonly name: string
}

function esquemaPara(maximo: number) {
  return z.object({
    name: z.string().superRefine((valor, contexto) => {
      const problema = problemaDelNombre(valor, maximo)
      if (problema !== null) {
        contexto.addIssue({ code: 'custom', message: problema })
      }
    }),
  })
}

// Muestra cómo va a quedar el nombre, así nadie se sorprende al ver la lista.
function pista(nombre: string): string {
  const escrito = nombre.split(/\s+/u).filter(Boolean).join(' ')
  const formateado = formatearNombreDeCatalogo(nombre)
  if (formateado === '' || formateado === escrito) {
    return 'Mayúscula solo al inicio. Un nombre propio, como «Perú», la conserva si el resto va en minúscula.'
  }
  return `Se guardará como «${formateado}».`
}

/** Agrega o corrige un nombre del catálogo. */
export default function CatalogEntryForm(props: CatalogEntryFormProps) {
  const { register, handleSubmit, control, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquemaPara(props.maxLength)),
    defaultValues: { name: props.initialName ?? '' },
  })
  const nombre = useWatch({ control, name: 'name' })
  const guardado = useCatalogChange(props.onSave)
  const coincidencias = buscarCoincidencias(nombre, props.existing)

  return (
    <form
      noValidate
      className="flex flex-col gap-3"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          guardado.mutate(valores.name, {
            onSuccess: () => {
              reset({ name: '' })
              props.onClose()
            },
          })
        }),
      )}
    >
      <TextField
        id={props.id}
        label={props.label}
        placeholder={props.placeholder}
        icon={props.icon}
        field={register('name')}
        error={formState.errors.name?.message}
        hint={pista(nombre)}
      />
      <SimilarNames coincidencias={coincidencias} />
      {guardado.isError ? (
        <FormMessage tone="error">{errorMessage(guardado.error, 'No se pudo guardar.')}</FormMessage>
      ) : null}
      <DialogFormActions>
        <Button type="button" variant="outline" size="lg" className="h-10 px-4" onClick={props.onClose}>
          Cancelar
        </Button>
        <Button
          type="submit"
          size="lg"
          className="h-10 px-4"
          disabled={guardado.isPending || coincidencias.exacto !== undefined}
        >
          <Icon name={props.initialName === undefined ? 'agregar' : 'confirmar'} size={16} />
          <span>{guardado.isPending ? 'Guardando…' : props.submitLabel}</span>
        </Button>
      </DialogFormActions>
    </form>
  )
}
