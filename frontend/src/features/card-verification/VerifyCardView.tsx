import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router'

import { fetchPublicVaccinationCard, publicVaccinationCardQueryKey } from '../../api/medicalRecords'
import EmptyState from '../../components/EmptyState'
import PageHeader from '../../components/PageHeader'
import SectionCard from '../../components/SectionCard'
import VaccineStatusList from '../../components/VaccineStatusList'
import { formatearFechaDeVacuna } from '../../components/vaccineDates'

/**
 * Lo que ve quien escanea el QR de un carnet de vacunas.
 *
 * Una municipalidad u otra veterinaria confirma las vacunas sin cuenta y sin
 * ver ningún dato de la persona dueña. El estado es el de hoy, no el del día
 * en que se imprimió el carnet.
 */
export default function VerifyCardView() {
  const { token = '' } = useParams()
  const carnet = useQuery({
    queryKey: publicVaccinationCardQueryKey(token),
    queryFn: () => fetchPublicVaccinationCard(token),
    retry: false,
  })
  const datos = carnet.data

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 py-8">
      <PageHeader
        title="Verificación de carnet de vacunas"
        description="Datos registrados en la clínica. No incluye información del dueño."
      />
      {carnet.isPending ? <EmptyState title="Verificando el carnet…" /> : null}
      {carnet.isError ? (
        <EmptyState
          title="Este carnet no es válido o ya venció."
          description="Pide a la clínica o al dueño un carnet nuevo."
        />
      ) : null}
      {datos === undefined ? null : (
        <SectionCard
          title={datos.pet_name}
          description={`${datos.species} · ${datos.breed} · Microchip: ${datos.microchip_number || 'no registrado'}`}
        >
          {datos.summary.length === 0 ? (
            <EmptyState title="No tiene vacunas registradas." />
          ) : (
            <VaccineStatusList summary={datos.summary} />
          )}
          <p className="m-0 text-sm text-muted-foreground">
            Estado al {formatearFechaDeVacuna(datos.checked_on)}. Este enlace de verificación vence el{' '}
            {formatearFechaDeVacuna(datos.valid_until)}.
          </p>
        </SectionCard>
      )}
    </div>
  )
}
