import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { myPetsQueryKey, registerPet } from '../../api/pets'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SectionCard from '../../components/SectionCard'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

const esquema = z.object({
  name: z.string().min(1, 'Ingresá el nombre'),
  species: z.string().min(1, 'Ingresá la especie'),
  breed: z.string().min(1, 'Ingresá la raza'),
  birth_date: z.string().min(1, 'Ingresá la fecha de nacimiento'),
})

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = { name: '', species: '', breed: '', birth_date: '' }

export default function PetForm() {
  const queryClient = useQueryClient()
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })
  const errores = formState.errors

  const alta = useMutation({
    mutationFn: registerPet,
    onSuccess: async () => {
      reset(VACIO)
      await queryClient.invalidateQueries({ queryKey: myPetsQueryKey })
    },
  })

  return (
    <SectionCard title="Registrar una mascota">
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
          <TextField id="name" label="Nombre" field={register('name')} error={errores.name?.message} />
          <TextField
            id="species"
            label="Especie"
            placeholder="Perro, gato, conejo…"
            field={register('species')}
            error={errores.species?.message}
          />
          <TextField id="breed" label="Raza" field={register('breed')} error={errores.breed?.message} />
          <TextField
            id="birth_date"
            label="Fecha de nacimiento"
            type="date"
            field={register('birth_date')}
            error={errores.birth_date?.message}
          />
        </div>

        {alta.isError ? (
          <FormMessage tone="error">
            {errorMessage(alta.error, 'No se pudo registrar la mascota.')}
          </FormMessage>
        ) : null}

        <Button
          type="submit"
          variant="success"
          size="lg"
          className="h-10 self-start px-4"
          disabled={alta.isPending}
        >
          <Icon name="agregar" size={16} />
          <span>{alta.isPending ? 'Guardando…' : 'Registrar'}</span>
        </Button>
      </form>
    </SectionCard>
  )
}
