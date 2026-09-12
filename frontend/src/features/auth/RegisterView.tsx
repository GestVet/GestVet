import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router'
import { z } from 'zod'

import { login, registerClient } from '../../api/auth'
import FieldError from '../../components/FieldError'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import { useSession } from '../../store/session'

// La longitud minima la exige tambien el backend. Repetirla aca no es
// duplicar la regla: es avisar antes de gastar un viaje al servidor.
const MIN_PASSWORD = 10

const esquema = z.object({
  first_name: z.string().min(1, 'Ingresá tu nombre'),
  last_name: z.string().min(1, 'Ingresá tu apellido'),
  email: z.email('Ingresá un correo válido'),
  phone: z.string().max(32).optional(),
  document_id: z.string().regex(/^\d{8}$/, 'El DNI tiene 8 dígitos'),
  password: z.string().min(MIN_PASSWORD, `Usá al menos ${String(MIN_PASSWORD)} caracteres`),
})

type Formulario = z.infer<typeof esquema>

export default function RegisterView() {
  const signIn = useSession((state) => state.signIn)
  const navigate = useNavigate()
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      document_id: '',
      password: '',
    },
  })

  const crear = useMutation({
    mutationFn: async (valores: Formulario) => {
      await registerClient({ ...valores, phone: valores.phone ?? '' })
      // El alta no devuelve token: se entra con las mismas credenciales.
      return login({ email: valores.email, password: valores.password })
    },
    onSuccess: (respuesta) => {
      signIn(respuesta)
      void navigate('/panel')
    },
  })

  return (
    <section className="card form">
      <h1>Crear una cuenta</h1>
      <p className="muted">El registro crea una cuenta de cliente.</p>

      <form className="form" onSubmit={onSubmit(
          handleSubmit((valores) => {
            crear.mutate(valores)
          }),
        )}>
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
          <input id="email" type="email" autoComplete="email" {...register('email')} />
          <FieldError message={formState.errors.email?.message} />
        </div>

        <div className="field">
          <label htmlFor="phone">Teléfono</label>
          <input id="phone" inputMode="tel" {...register('phone')} />
        </div>

        <div className="field">
          <label htmlFor="document_id">DNI</label>
          <input id="document_id" inputMode="numeric" maxLength={8} {...register('document_id')} />
          <FieldError message={formState.errors.document_id?.message} />
        </div>

        <div className="field">
          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            {...register('password')}
          />
          <FieldError message={formState.errors.password?.message} />
        </div>

        {crear.isError ? (
          <FormMessage tone="error">{errorMessage(crear.error, 'No se pudo crear la cuenta.')}</FormMessage>
        ) : null}

        <button type="submit" className="btn btn-green" disabled={crear.isPending}>
          <Icon name="agregar" size={16} />
          <span>{crear.isPending ? 'Creando…' : 'Crear cuenta'}</span>
        </button>
      </form>
    </section>
  )
}
