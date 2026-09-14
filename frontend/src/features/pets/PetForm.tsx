import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'

import { myPetsQueryKey, registerPet } from '../../api/pets'
import DialogFormActions from '../../components/DialogFormActions'
import FormMessage from '../../components/FormMessage'
import {
  fechaDeNacimientoRule,
  limitesDeNacimiento,
  MAX_NOMBRE_DE_MASCOTA,
  nombreDeMascotaRule,
} from '../../components/formRules'
import Icon from '../../components/Icon'
import SpeciesBreedFields from '../../components/SpeciesBreedFields'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const esquema = z.object({
  name: nombreDeMascotaRule,
  species: z.string().min(1, 'Elige la especie'),
  breed: z.string().min(1, 'Elige la raza'),
  birth_date: fechaDeNacimientoRule,
})

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = { name: '', species: '', breed: '', birth_date: '' }

interface PetFormProps {
  /** Se llama al registrarla o al cancelar: cierra la ventana. */
  readonly onDone: () => void
}

export default function PetForm({ onDone }: PetFormProps) {
  const queryClient = useQueryClient()
  const { register, handleSubmit, formState, control, setValue } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })
  const especie = useWatch({ control, name: 'species' })
  const errores = formState.errors
  const limites = limitesDeNacimiento()

  const alta = useMutation({
    mutationFn: registerPet,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: myPetsQueryKey })
      onDone()
    },
  })

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={onSubmit(
        handleSubmit((valores) => {
          alta.mutate(valores)
        }),
      )}
    >
      <div className="grid gap-5 sm:grid-cols-2">
        <TextField
          id="name"
          label="Nombre"
          placeholder="Firulais"
          icon="mascota"
          maxLength={MAX_NOMBRE_DE_MASCOTA}
          field={register('name')}
          error={errores.name?.message}
        />
        <TextField
          id="birth_date"
          label="Fecha de nacimiento"
          type="date"
          min={limites.min}
          max={limites.max}
          hint="Si no la sabes exacta, pon una aproximada."
          field={register('birth_date')}
          error={errores.birth_date?.message}
        />
        <SpeciesBreedFields
          idPrefix="mascota"
          species={especie}
          speciesField={register('species', {
            // Otra especie tiene otras razas: la elegida deja de valer.
            onChange: () => {
              setValue('breed', '')
            },
          })}
          speciesError={errores.species?.message}
          breedField={register('breed')}
          breedError={errores.breed?.message}
        />
      </div>

      {alta.isError ? (
        <FormMessage tone="error">
          {errorMessage(alta.error, 'No se pudo registrar la mascota.')}
        </FormMessage>
      ) : null}

      <DialogFormActions>
        <Button type="button" variant="outline" size="lg" className="h-10 px-4" onClick={onDone}>
          Cancelar
        </Button>
        <Button type="submit" variant="success" size="lg" className="h-10 px-4" disabled={alta.isPending}>
          <Icon name="agregar" size={16} />
          <span>{alta.isPending ? 'Guardando…' : 'Registrar mascota'}</span>
        </Button>
      </DialogFormActions>
    </form>
  )
}
