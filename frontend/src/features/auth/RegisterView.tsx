import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router'

import { login, registerClient } from '../../api/auth'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import { Button } from '../../components/ui/button'
import { onSubmit } from '../../hooks/formSubmit'
import { useIdentityCheck } from '../../hooks/useIdentityCheck'
import { errorMessage } from '../../services/api'
import { useSession } from '../../store/session'
import AuthAside from './AuthAside'
import AuthCard from './AuthCard'
import RegisterFields from './RegisterFields'
import {
  type RegisterForm,
  registerSchema,
  registerSchemaWithIdentityCheck,
} from './registerSchema'

const PANEL = (
  <AuthAside
    title="Con tu cuenta puedes"
    items={[
      { icon: 'mascota', text: 'Registrar a tus mascotas una sola vez.' },
      { icon: 'cita', text: 'Reservar en los horarios libres de cada veterinario.' },
      { icon: 'emergencia', text: 'Abrir una emergencia a cualquier hora del día.' },
      { icon: 'carpeta', text: 'Seguir la historia clínica de cada mascota.' },
    ]}
    note="Con tu DNI te identificamos al llegar a la clínica."
  />
)

export default function RegisterView() {
  const signIn = useSession((state) => state.signIn)
  const navigate = useNavigate()
  const verificaDni = useIdentityCheck()
  const { register, handleSubmit, formState, control } = useForm<RegisterForm>({
    resolver: zodResolver(verificaDni ? registerSchemaWithIdentityCheck : registerSchema),
    mode: 'onTouched',
    defaultValues: {
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      document_id: '',
      password: '',
      accepts_identity_check: false,
      accepts_terms: false,
    },
  })

  const crear = useMutation({
    mutationFn: async (valores: RegisterForm) => {
      await registerClient({ ...valores, accepts_terms: true })
      // El alta no devuelve token: se entra con las mismas credenciales.
      return login({ email: valores.email, password: valores.password })
    },
    onSuccess: (respuesta) => {
      signIn(respuesta)
      void navigate('/panel')
    },
  })

  return (
    <AuthCard
      title="Crear una cuenta"
      description="Para dueños de mascotas. Si trabajas en la clínica, la administración crea tu cuenta."
      aside={PANEL}
      footer={
        <p className="m-0 text-muted-foreground">
          ¿Ya tienes cuenta?{' '}
          <Link
            to="/acceso"
            className="inline-flex items-center min-h-[32px] rounded-sm font-medium text-primary underline underline-offset-4 outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            Inicia sesión
          </Link>
        </p>
      }
    >
      <form
        noValidate
        className="flex flex-col gap-5"
        onSubmit={onSubmit(
          handleSubmit((valores) => {
            crear.mutate(valores)
          }),
        )}
      >
        <RegisterFields register={register} control={control} errors={formState.errors} />

        {crear.isError ? (
          <FormMessage tone="error">
            {errorMessage(crear.error, 'No se pudo crear la cuenta. Inténtalo de nuevo.')}
          </FormMessage>
        ) : null}

        <Button type="submit" size="lg" className="h-11 w-full" disabled={crear.isPending}>
          <Icon name="registrarse" size={18} />
          <span>{crear.isPending ? 'Creando tu cuenta…' : 'Crear cuenta'}</span>
        </Button>
      </form>
    </AuthCard>
  )
}
