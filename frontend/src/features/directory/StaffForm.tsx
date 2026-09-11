import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { registerStaff, staffQueryKey } from '../../api/directory'
import FieldError from '../../components/FieldError'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'

// La longitud mínima la exige también el backend. Repetirla no duplica la
// regla: avisa antes de gastar un viaje al servidor.
const MIN_PASSWORD = 10

const esquema = z.object({
  first_name: z.string().min(1, 'Ingresá el nombre'),
  last_name: z.string().min(1, 'Ingresá el apellido'),
  email: z.email('Ingresá un correo válido'),
  phone: z.string().max(32).optional(),
  password: z.string().min(MIN_PASSWORD, `Usá al menos ${String(MIN_PASSWORD)} caracteres`),
  role: z.enum(['veterinarian', 'emergency_veterinarian']),
})

type Formulario = z.infer<typeof esquema>

const VACIO: Formulario = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  password: '',
  role: 'veterinarian',
}

export default function StaffForm() {
  const queryClient = useQueryClient()
  const { register, handleSubmit, reset, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: VACIO,
  })

  const alta = useMutation({
    mutationFn: (valores: Formulario) => registerStaff({ ...valores, phone: valores.phone ?? '' }),
    onSuccess: async () => {
      reset(VACIO)
      await queryClient.invalidateQueries({ queryKey: staffQueryKey })
    },
  })

  return (
    <section className="card">
      <h2>Dar de alta un veterinario</h2>
      <form
        className="form"
        onSubmit={onSubmit(
          handleSubmit((valores) => {
            alta.mutate(valores)
          }),
        )}
      >
        <div className="field">
          <label htmlFor="first_name">Nombre</label>
          <input id="first_name" {...register('first_name')} />
          <FieldError message={formState.errors.first_name?.message} />
        </div>

        <div className="field">
          <label htmlFor="last_name">Apellido</label>
          <input id="last_name" {...register('last_name')} />
          <FieldError message={formState.errors.last_name?.message} />
        </div>

        <div className="field">
          <label htmlFor="email">Correo</label>
          <input id="email" type="email" {...register('email')} />
          <FieldError message={formState.errors.email?.message} />
        </div>

        <div className="field">
          <label htmlFor="phone">Teléfono</label>
          <input id="phone" inputMode="tel" {...register('phone')} />
        </div>

        <div className="field">
          <label htmlFor="password">Contraseña inicial</label>
          <input id="password" type="password" {...register('password')} />
          <FieldError message={formState.errors.password?.message} />
        </div>

        <div className="field">
          <label htmlFor="role">Rol</label>
          <select id="role" {...register('role')}>
            <option value="veterinarian">Veterinario</option>
            <option value="emergency_veterinarian">Veterinario de guardia</option>
          </select>
        </div>

        {alta.isError ? (
          <FormMessage tone="error">
            {errorMessage(alta.error, 'No se pudo dar de alta la cuenta.')}
          </FormMessage>
        ) : null}

        <button type="submit" className="btn btn-green" disabled={alta.isPending}>
          <Icon name="agregar" size={16} />
          <span>{alta.isPending ? 'Creando…' : 'Dar de alta'}</span>
        </button>
      </form>
    </section>
  )
}
