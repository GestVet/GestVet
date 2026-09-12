import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { updateProfile } from '../../api/auth'
import type { UserResponse } from '../../api/types'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import TextField from '../../components/TextField'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import { useSession } from '../../store/session'

// La longitud mínima la exige también el backend. Repetirla no duplica la
// regla: avisa antes de gastar un viaje al servidor.
const MIN_PASSWORD = 10

const esquema = z.object({
  first_name: z.string().min(1, 'Ingresá tu nombre'),
  last_name: z.string().min(1, 'Ingresá tu apellido'),
  phone: z.string().max(32),
  document_id: z.string().regex(/^\d{8}$/, 'El DNI tiene 8 dígitos').or(z.literal('')),
  // Vacía significa "conservar la actual", así que la longitud solo se exige
  // cuando el campo trae algo.
  new_password: z
    .string()
    .min(MIN_PASSWORD, `Usá al menos ${String(MIN_PASSWORD)} caracteres`)
    .or(z.literal('')),
})

type Formulario = z.infer<typeof esquema>

/**
 * Valores de partida del formulario.
 *
 * Vive fuera del componente porque cada `??` cuenta para la complejidad, y
 * cuatro campos con respaldo se comian el presupuesto entero de la vista.
 */
function valoresIniciales(user: UserResponse | null): Formulario {
  return {
    first_name: user?.first_name ?? '',
    last_name: user?.last_name ?? '',
    phone: user?.phone ?? '',
    document_id: user?.document_id ?? '',
    new_password: '',
  }
}

export default function ProfileView() {
  const user = useSession((state) => state.user)
  const updateUser = useSession((state) => state.updateUser)

  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: valoresIniciales(user),
  })

  const guardar = useMutation({
    mutationFn: (valores: Formulario) =>
      updateProfile({
        first_name: valores.first_name,
        last_name: valores.last_name,
        phone: valores.phone,
        document_id: valores.document_id,
        new_password: valores.new_password === '' ? null : valores.new_password,
      }),
    onSuccess: updateUser,
  })

  const errores = formState.errors

  return (
    <section className="card form">
      <h1>Mi perfil</h1>
      <p className="muted">{user?.email} · el correo y el rol no se editan desde acá.</p>

      <form
        className="form"
        onSubmit={onSubmit(
          handleSubmit((valores) => {
            guardar.mutate(valores)
          }),
        )}
      >
        <TextField
          id="first_name"
          label="Nombre"
          field={register('first_name')}
          error={errores.first_name?.message}
        />
        <TextField
          id="last_name"
          label="Apellido"
          field={register('last_name')}
          error={errores.last_name?.message}
        />
        <TextField
          id="phone"
          label="Teléfono"
          inputMode="tel"
          field={register('phone')}
          error={errores.phone?.message}
        />
        <TextField
          id="document_id"
          label="DNI"
          inputMode="numeric"
          field={register('document_id')}
          error={errores.document_id?.message}
        />
        <TextField
          id="new_password"
          label="Nueva contraseña"
          type="password"
          autoComplete="new-password"
          hint="Dejala vacía para conservar la actual."
          field={register('new_password')}
          error={errores.new_password?.message}
        />

        {guardar.isError ? (
          <FormMessage tone="error">
            {errorMessage(guardar.error, 'No se pudo guardar el perfil.')}
          </FormMessage>
        ) : null}
        {guardar.isSuccess ? <FormMessage tone="ok">Perfil actualizado.</FormMessage> : null}

        <button type="submit" className="btn btn-blue" disabled={guardar.isPending}>
          <Icon name="confirmar" size={16} />
          <span>{guardar.isPending ? 'Guardando…' : 'Guardar'}</span>
        </button>
      </form>
    </section>
  )
}
