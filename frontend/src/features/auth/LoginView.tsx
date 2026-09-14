import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router'
import { z } from 'zod'

import { login } from '../../api/auth'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import PasswordField from '../../components/PasswordField'
import TextField from '../../components/TextField'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { errorMessage } from '../../services/api'
import { useSession } from '../../store/session'
import AuthAside from './AuthAside'
import AuthCard from './AuthCard'
import { correoRule } from '../../services/fieldRules'
import SessionExpiredNotice from './SessionExpiredNotice'

const esquema = z.object({
  email: correoRule,
  // Al entrar no se exige la longitud: una cuenta antigua puede tener una
  // contrasena mas corta, y la respuesta del servidor ya dice si no coincide.
  password: z.string().min(1, 'Escribe tu contraseña'),
})

type Formulario = z.infer<typeof esquema>

const PANEL = (
  <AuthAside
    title="Todo sobre tu mascota, en un solo lugar"
    items={[
      { icon: 'cita', text: 'Reserva y cancela tus citas desde tu cuenta.' },
      { icon: 'carpeta', text: 'Consulta la historia clínica de cada mascota.' },
      { icon: 'pago', text: 'Paga tus citas con QR.' },
    ]}
    note="Si trabajas en la clínica, entra con la cuenta que te creó la administración."
  />
)

const ENLACE = 'font-medium text-primary underline underline-offset-4'

/**
 * A dónde ir después de entrar.
 *
 * La guarda de rutas deja la pantalla que se quiso abrir: quien vuelve tras una
 * sesión vencida sigue donde estaba en vez de empezar desde el panel.
 */
function destinoDe(estado: unknown): string {
  const desde =
    typeof estado === 'object' && estado !== null && 'from' in estado ? estado.from : undefined
  return typeof desde === 'string' && desde.startsWith('/') && desde !== '/acceso' ? desde : '/panel'
}

export default function LoginView() {
  const signIn = useSession((state) => state.signIn)
  const navigate = useNavigate()
  const destino = destinoDe(useLocation().state)
  const { register, handleSubmit, formState } = useForm<Formulario>({
    resolver: zodResolver(esquema),
    mode: 'onTouched',
    defaultValues: { email: '', password: '' },
  })

  const acceder = useMutation({
    mutationFn: login,
    onSuccess: (respuesta) => {
      signIn(respuesta)
      void navigate(destino, { replace: true })
    },
  })

  return (
    <AuthCard
      title="Iniciar sesión"
      aside={PANEL}
      footer={
        <p className="m-0 text-muted-foreground">
          ¿No tienes cuenta?{' '}
          <Link to="/registro" className={ENLACE}>
            Regístrate
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
        <SessionExpiredNotice />
        <TextField
          id="email"
          label="Correo"
          placeholder="nombre@correo.com"
          type="email"
          inputMode="email"
          autoComplete="email"
          spellCheck={false}
          field={register('email')}
          error={formState.errors.email?.message}
        />

        <div className="flex flex-col gap-2">
          <PasswordField
            id="password"
            label="Contraseña"
            placeholder="Tu contraseña"
            autoComplete="current-password"
            field={register('password')}
            error={formState.errors.password?.message}
          />
          <Link to="/olvide-contrasena" className={`self-end text-sm ${ENLACE}`}>
            ¿Olvidaste tu contraseña?
          </Link>
        </div>

        {acceder.isError ? (
          <FormMessage tone="error">
            {errorMessage(acceder.error, 'No se pudo iniciar sesión. Inténtalo de nuevo.')}
          </FormMessage>
        ) : null}

        <Button type="submit" size="lg" className="h-11 w-full" disabled={acceder.isPending}>
          <Icon name="entrar" size={18} />
          <span>{acceder.isPending ? 'Entrando…' : 'Entrar'}</span>
        </Button>
      </form>
    </AuthCard>
  )
}
