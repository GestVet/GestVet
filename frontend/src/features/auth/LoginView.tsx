import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router'
import { z } from 'zod'

import { login } from '../../api/auth'
import FieldError from '../../components/FieldError'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import { useSession } from '../../store/session'

const esquema = z.object({
  email: z.email('Ingresá un correo válido'),
  password: z.string().min(1, 'Ingresá tu contraseña'),
})

type Formulario = z.infer<typeof esquema>

export default function LoginView() {
  const signIn = useSession((state) => state.signIn)
  const navigate = useNavigate()
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    defaultValues: { email: '', password: '' },
  })

  const acceder = useMutation({
    mutationFn: login,
    onSuccess: (respuesta) => {
      signIn(respuesta)
      void navigate('/panel')
    },
  })

  return (
    <section className="card form">
      <h1>Iniciar sesión</h1>
      <form className="form" onSubmit={onSubmit(
          handleSubmit((valores) => {
            acceder.mutate(valores)
          }),
        )}>
        <div className="field">
          <label htmlFor="email">Correo</label>
          <input id="email" type="email" autoComplete="email" {...register('email')} />
          <FieldError message={formState.errors.email?.message} />
        </div>

        <div className="field">
          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            {...register('password')}
          />
          <FieldError message={formState.errors.password?.message} />
        </div>

        {acceder.isError ? (
          <FormMessage tone="error">{errorMessage(acceder.error, 'No se pudo iniciar sesión.')}</FormMessage>
        ) : null}

        <button type="submit" className="btn btn-blue" disabled={acceder.isPending}>
          <Icon name="confirmar" size={16} />
          <span>{acceder.isPending ? 'Entrando…' : 'Entrar'}</span>
        </button>
      </form>
    </section>
  )
}
