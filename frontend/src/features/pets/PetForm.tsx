import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { myPetsQueryKey, registerPet } from '../../api/pets'
import { OTHER_SPECIES_OPTION } from '../../components/petSpecies'
import FieldError from '../../components/FieldError'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SpeciesField from '../../components/SpeciesField'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const esquema = z
  .object({
    name: z.string().min(1, 'Ingresá el nombre'),
    species: z.string().min(1, 'Elegí la especie'),
    species_other: z.string().optional(),
    breed: z.string().min(1, 'Ingresá la raza'),
    birth_date: z.string().min(1, 'Ingresá la fecha de nacimiento'),
  })
  .refine((valores) => valores.species !== OTHER_SPECIES_OPTION || !!valores.species_other?.trim(), {
    message: 'Contanos cuál es',
    path: ['species_other'],
  })

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = {
  name: '',
  species: '',
  species_other: '',
  breed: '',
  birth_date: '',
}

export default function PetForm() {
  const queryClient = useQueryClient()
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })

  const alta = useMutation({
    mutationFn: (valores: Formulario) =>
      registerPet({
        name: valores.name,
        species:
          valores.species === OTHER_SPECIES_OPTION
            ? (valores.species_other ?? '')
            : valores.species,
        breed: valores.breed,
        birth_date: valores.birth_date,
      }),
    onSuccess: async () => {
      reset(VACIO)
      await queryClient.invalidateQueries({ queryKey: myPetsQueryKey })
    },
  })

  return (
    <section className="card">
      <h2>Registrar una mascota</h2>
      <form
        className="form"
        onSubmit={onSubmit(
          handleSubmit((valores) => {
            alta.mutate(valores)
          }),
        )}
      >
        <div className="field">
          <label htmlFor="name">Nombre</label>
          <input id="name" {...register('name')} />
          <FieldError message={formState.errors.name?.message} />
        </div>

        <SpeciesField
          speciesId="species"
          otherId="species_other"
          speciesField={register('species')}
          otherField={register('species_other')}
          speciesError={formState.errors.species?.message}
          otherError={formState.errors.species_other?.message}
          initiallyOther={false}
        />

        <div className="field">
          <label htmlFor="breed">Raza</label>
          <input id="breed" {...register('breed')} />
          <FieldError message={formState.errors.breed?.message} />
        </div>

        <div className="field">
          <label htmlFor="birth_date">Fecha de nacimiento</label>
          <input id="birth_date" type="date" {...register('birth_date')} />
          <FieldError message={formState.errors.birth_date?.message} />
        </div>

        {alta.isError ? (
          <FormMessage tone="error">
            {errorMessage(alta.error, 'No se pudo registrar la mascota.')}
          </FormMessage>
        ) : null}

        <button type="submit" className="btn btn-green" disabled={alta.isPending}>
          <Icon name="agregar" size={16} />
          <span>{alta.isPending ? 'Guardando…' : 'Registrar'}</span>
        </button>
      </form>
    </section>
  )
}
