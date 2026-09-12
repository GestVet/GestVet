import type { UserResponse } from '../../api/types'
import SectionHeading from '../../components/SectionHeading'
import { hasPendingContact } from './clientContact'
import ClientPets from './ClientPets'
import CompleteContactForm from './CompleteContactForm'

interface ClientDetailsProps {
  readonly cliente: UserResponse
}

/**
 * Lo que se despliega bajo un cliente.
 *
 * Si vino por el alta exprés de emergencia, primero el formulario para
 * completar su correo real, que es lo que le falta para poder entrar.
 */
export default function ClientDetails({ cliente }: ClientDetailsProps) {
  return (
    <div className="flex flex-col gap-6">
      {hasPendingContact(cliente) ? (
        <div className="flex flex-col gap-3">
          <SectionHeading as="h2">Completar contacto</SectionHeading>
          <CompleteContactForm clientId={cliente.id} phone={cliente.phone} />
        </div>
      ) : null}
      <div className="flex flex-col gap-3">
        <SectionHeading as="h2">
          Mascotas de {cliente.first_name} {cliente.last_name}
        </SectionHeading>
        <ClientPets ownerId={cliente.id} />
      </div>
    </div>
  )
}
