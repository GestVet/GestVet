import { Link } from 'react-router'

import FormMessage from '../../components/FormMessage'
import AuthCard from './AuthCard'

/** Lo que ve quien abre el enlace de recuperacion sin el codigo. */
export default function MissingResetToken() {
  return (
    <AuthCard
      title="Restablecer contraseña"
      footer={
        <Link
          to="/olvide-contrasena"
          className="inline-flex items-center min-h-[32px] rounded-sm font-medium text-primary underline underline-offset-4 outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          Pedir un enlace nuevo
        </Link>
      }
    >
      <FormMessage tone="error">
        El enlace no trae el código de recuperación. Pide uno nuevo.
      </FormMessage>
    </AuthCard>
  )
}
