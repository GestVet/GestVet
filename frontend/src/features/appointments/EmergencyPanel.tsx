import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { fetchMyPets, myPetsQueryKey } from '../../api/pets'
import FormDialog from '../../components/FormDialog'
import FormMessage from '../../components/FormMessage'
import Icon from '../../components/Icon'
import SectionCard from '../../components/SectionCard'
import { Button } from '../../components/ui/button'
import { useSession } from '../../store/session'
import EmergencyForm from './EmergencyForm'

/**
 * El acceso del cliente a una emergencia.
 *
 * El botón abre una ventana donde elige la mascota, cuenta qué le pasa y
 * acepta el riesgo. Es lo único que se le pide: nada de eso frena la
 * atención, que empieza apenas llega a la clínica.
 */
export default function EmergencyPanel() {
  const mascotas = useQuery({ queryKey: myPetsQueryKey, queryFn: fetchMyPets })
  const usuario = useSession((estado) => estado.user)
  const [abierto, setAbierto] = useState(false)
  const [abierta, setAbierta] = useState(false)

  const activas = mascotas.data?.items.filter((mascota) => mascota.is_active) ?? []
  const firmante = usuario === null ? '' : `${usuario.first_name} ${usuario.last_name}`.trim()

  return (
    <SectionCard
      title="Emergencia"
      description="No se elige hora ni veterinario. El sistema asigna al que esté de guardia en este momento."
    >
      {abierta ? (
        <FormMessage tone="ok">Emergencia abierta. Acércate a la clínica.</FormMessage>
      ) : null}

      <Button
        type="button"
        variant="danger"
        size="lg"
        className="h-11 w-full px-4 whitespace-normal"
        disabled={activas.length === 0}
        onClick={() => {
          setAbierta(false)
          setAbierto(true)
        }}
      >
        <Icon name="emergencia" size={16} />
        <span>Abrir emergencia</span>
      </Button>

      <FormDialog
        open={abierto}
        onOpenChange={setAbierto}
        title="Abrir una emergencia"
        description="Lee el texto y acéptalo. La atención empieza apenas llegues a la clínica."
      >
        <EmergencyForm
          pets={activas}
          signerName={firmante}
          onCancel={() => {
            setAbierto(false)
          }}
          onOpened={() => {
            setAbierto(false)
            setAbierta(true)
          }}
        />
      </FormDialog>
    </SectionCard>
  )
}
