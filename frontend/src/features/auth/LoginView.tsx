import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router'
import { z } from 'zod'

import { login } from '../../api/auth'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import { useSession } from '../../store/session'
import AuthCard from './AuthCard'

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
    <AuthCard
      title="Iniciar sesión"
      footer={
        <p className="m-0 text-muted-foreground">
          ¿No tenés cuenta?{' '}
          <Link to="/registro" className="font-medium text-primary underline underline-offset-4">
            Registrate
          </Link>
        </p>
      }
    >
      <form
        noValidate
        className="flex flex-col gap-5"
        onSubmit={onSubmit(
          handleSubmit((valores) => {
            acceder.mutate(valores)
          }),
        )}
      >
        <TextField
          id="email"
          label="Correo"
          type="email"
          autoComplete="email"
          field={register('email')}
          error={formState.errors.email?.message}
        />

        <div className="flex flex-col gap-2">
          <TextField
            id="password"
            label="Contraseña"
            type="password"
            autoComplete="current-password"
            field={register('password')}
            error={formState.errors.password?.message}
          />
          <Link
            to="/olvide-contrasena"
            className="self-end text-sm font-medium text-primary underline underline-offset-4"
          >
            ¿Olvidaste tu contraseña?
          </Link>
        </div>

        {acceder.isError ? (
          <FormMessage tone="error">
            {errorMessage(acceder.error, 'No se pudo iniciar sesión.')}
          </FormMessage>
        ) : null}

        <Button type="submit" size="lg" className="h-10 w-full" disabled={acceder.isPending}>
          <Icon name="confirmar" size={16} />
          <span>{acceder.isPending ? 'Entrando…' : 'Entrar'}</span>
        </Button>
      </form>
    </AuthCard>
  )
}
