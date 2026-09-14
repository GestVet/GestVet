import type { UserResponse } from '../../api/types'

// El dominio de relleno que usa el alta exprés de emergencia: mientras el
// correo de un cliente termine así, esa cuenta no puede entrar por su cuenta.
const PLACEHOLDER_EMAIL_SUFFIX = '@pendiente.gestvet.local'

export function hasPendingContact(cliente: Pick<UserResponse, 'email'>): boolean {
  return cliente.email.endsWith(PLACEHOLDER_EMAIL_SUFFIX)
}
