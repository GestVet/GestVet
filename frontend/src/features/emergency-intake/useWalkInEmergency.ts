import { useMutation, useQuery } from '@tanstack/react-query'
import { useRef } from 'react'

import { openWalkInEmergency } from '../../api/appointments'
import {
  currentTemplateQueryKey,
  fetchCurrentTemplate,
  recordInPersonEmergencyRisk,
} from '../../api/consents'
import { registerWalkInClient } from '../../api/directory'
import { registerPetForOwner } from '../../api/pets'
import type { AppointmentResponse } from '../../api/types'
import { errorStatus } from '../../services/api'
import type { WalkInEmergencyFormValues } from './formValues'

// El servidor rechaza la firma para esta emergencia: vencida o ya usada.
const FIRMA_RECHAZADA = 422

/**
 * Alta exprés: cliente, mascota, aceptación del riesgo y emergencia.
 *
 * Son cuatro llamadas seguidas porque cada módulo es dueño de su propia
 * escritura: no hay una transacción única detrás. Si una llamada intermedia
 * falla, los identificadores ya obtenidos quedan guardados acá, así que
 * reintentar no vuelve a crear lo que ya se creó ni pide otra firma.
 */
export function useWalkInEmergency(onSuccess: (cita: AppointmentResponse) => void) {
  const clienteId = useRef<number | null>(null)
  const mascotaId = useRef<number | null>(null)
  const consentimientoId = useRef<number | null>(null)
  const plantilla = useQuery({
    queryKey: currentTemplateQueryKey('emergency_risk'),
    queryFn: () => fetchCurrentTemplate('emergency_risk'),
  })

  const abrir = useMutation({
    mutationFn: async (valores: WalkInEmergencyFormValues) => {
      clienteId.current ??= (
        await registerWalkInClient({
          first_name: valores.first_name,
          last_name: valores.last_name,
          document_id: valores.document_id,
          phone: valores.phone,
        })
      ).id
      mascotaId.current ??= (
        await registerPetForOwner({
          owner_id: clienteId.current,
          name: valores.pet_name,
          species: valores.pet_species,
        })
      ).id
      consentimientoId.current ??= (
        await recordInPersonEmergencyRisk({
          client_id: clienteId.current,
          pet_id: mascotaId.current,
          template_id: plantilla.data?.id ?? 0,
          signer_name: valores.signer_name,
          accepted: true,
        })
      ).id
      try {
        return await openWalkInEmergency({
          client_id: clienteId.current,
          pet_id: mascotaId.current,
          description: valores.description,
          risk_consent_id: consentimientoId.current,
        })
      } catch (error) {
        if (errorStatus(error) === FIRMA_RECHAZADA) {
          consentimientoId.current = null
        }
        throw error
      }
    },
    onSuccess,
  })

  const olvidar = () => {
    clienteId.current = null
    mascotaId.current = null
    consentimientoId.current = null
  }

  return { plantilla, abrir, olvidar }
}
