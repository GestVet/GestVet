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
          className="font-medium text-primary underline underline-offset-4"
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
