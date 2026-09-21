import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRef, useState } from 'react'

import { appointmentsQueryKey, openEmergency } from '../../api/appointments'
import {
  acceptEmergencyRisk,
  currentTemplateQueryKey,
  fetchCurrentTemplate,
} from '../../api/consents'
import type { AppointmentResponse } from '../../api/types'
import { errorStatus } from '../../services/api'
import type { EmergencyFormValues } from './emergencySchema'

// Lo que responde el servidor cuando la firma ya no sirve para esta
// emergencia (vencida, de otra mascota o ya usada) o cuando el texto cambió.
const FIRMA_RECHAZADA = 422
const TEXTO_CAMBIADO = 409
const CLAVE_DEL_TEXTO = currentTemplateQueryKey('emergency_risk')

interface Firma {
  readonly petId: number
  readonly consentId: number
}

/**
 * Firma la aceptación del riesgo y abre la emergencia con ella.
 *
 * Son dos módulos distintos del servidor y no hay una transacción única
 * detrás. Si la apertura falla (por ejemplo, nadie de guardia), la firma
 * queda guardada y reintentar no vuelve a pedirla. Se pide de nuevo solo si
 * cambia la mascota o si el servidor dice que esa firma ya no sirve.
 */
export function useSignedEmergency(onOpened: (cita: AppointmentResponse) => void) {
  const queryClient = useQueryClient()
  const firma = useRef<Firma | null>(null)
  const [firmado, setFirmado] = useState(false)
  const plantilla = useQuery({
    queryKey: CLAVE_DEL_TEXTO,
    queryFn: () => fetchCurrentTemplate('emergency_risk'),
  })

  const olvidarFirma = () => {
    firma.current = null
    setFirmado(false)
  }

  const firmar = async (valores: EmergencyFormValues, petId: number): Promise<number> => {
    if (firma.current?.petId === petId) {
      return firma.current.consentId
    }
    try {
      const consentimiento = await acceptEmergencyRisk({
        pet_id: petId,
        template_id: plantilla.data?.id ?? 0,
        signer_name: valores.signer_name,
        accepted: true,
      })
      firma.current = { petId, consentId: consentimiento.id }
      setFirmado(true)
      return consentimiento.id
    } catch (error) {
      if (errorStatus(error) === TEXTO_CAMBIADO) {
        await queryClient.invalidateQueries({ queryKey: CLAVE_DEL_TEXTO })
      }
      throw error
    }
  }

  const abrir = useMutation({
    mutationFn: async (valores: EmergencyFormValues) => {
      const petId = Number(valores.pet_id)
      const consentId = await firmar(valores, petId)
      try {
        return await openEmergency({
          pet_id: petId,
          description: valores.description,
          risk_consent_id: consentId,
        })
      } catch (error) {
        if (errorStatus(error) === FIRMA_RECHAZADA) {
          olvidarFirma()
        }
        throw error
      }
    },
    onSuccess: async (cita) => {
      await queryClient.invalidateQueries({ queryKey: appointmentsQueryKey })
      onOpened(cita)
    },
  })

  return { plantilla, abrir, firmado }
}
