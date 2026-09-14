import type { QueryClient, QueryKey } from '@tanstack/react-query'

import { appointmentsFilterQueryKey, fetchAppointments } from '../../api/appointments'
import { fetchMySlots, mySlotsQueryKey } from '../../api/availability'
import { complaintsQueryKey, fetchComplaints } from '../../api/complaints'
import {
  activityQueryKey,
  clientsQueryKey,
  fetchActivity,
  fetchClients,
  fetchStaff,
  staffQueryKey,
} from '../../api/directory'
import {
  careRemindersQueryKey,
  fetchCareReminders,
  fetchNoShowRisks,
  fetchPaymentAnomalies,
  fetchVeterinarianAlerts,
  noShowRisksQueryKey,
  paymentAnomaliesQueryKey,
  veterinarianAlertsQueryKey,
} from '../../api/insights'
import {
  fetchPaymentReport,
  fetchPayments,
  paymentReportQueryKey,
  paymentsQueryKey,
} from '../../api/payments'
import { fetchMyPets, myPetsQueryKey } from '../../api/pets'
import { hoyEnClinica, lunesDe, ventanaDeSemana } from '../../services/clinicTime'

interface Consulta {
  readonly queryKey: QueryKey
  readonly queryFn: () => Promise<unknown>
}

// Las consultas con que abre cada pantalla, con sus filtros iniciales.
//
// Tienen que coincidir con las de la vista: con otra clave, la precarga baja
// datos que la pantalla no usa y la tabla vuelve a pedirlos. Un filtro vacio
// se escribe `{}` porque React Query ignora las propiedades `undefined` al
// comparar claves, y asi es como las vistas arman el filtro sin valores.
const CONSULTAS_POR_RUTA: Readonly<Partial<Record<string, readonly Consulta[]>>> = {
  '/citas': [
    { queryKey: appointmentsFilterQueryKey({}), queryFn: () => fetchAppointments({}) },
  ],
  '/mascotas': [{ queryKey: myPetsQueryKey, queryFn: fetchMyPets }],
  '/agenda': [
    {
      // La semana se calcula al pasar por el menú, no al cargar el módulo: la
      // pestaña puede quedar abierta de un lunes al siguiente.
      get queryKey() {
        return [...mySlotsQueryKey, lunesDe(hoyEnClinica())]
      },
      queryFn: () => {
        const ventana = ventanaDeSemana(lunesDe(hoyEnClinica()))
        return fetchMySlots(ventana.desde, ventana.hasta)
      },
    },
  ],
  '/clientes': [{ queryKey: clientsQueryKey, queryFn: fetchClients }],
  '/personal': [{ queryKey: staffQueryKey, queryFn: fetchStaff }],
  '/pagos': [
    { queryKey: paymentReportQueryKey({}), queryFn: () => fetchPaymentReport({}) },
    { queryKey: paymentsQueryKey({}), queryFn: () => fetchPayments({}) },
  ],
  '/reclamos': [{ queryKey: complaintsQueryKey, queryFn: fetchComplaints }],
  '/indicadores': [
    { queryKey: careRemindersQueryKey, queryFn: fetchCareReminders },
    { queryKey: noShowRisksQueryKey, queryFn: fetchNoShowRisks },
    { queryKey: paymentAnomaliesQueryKey, queryFn: fetchPaymentAnomalies },
    { queryKey: veterinarianAlertsQueryKey, queryFn: fetchVeterinarianAlerts },
  ],
  '/movimientos': [{ queryKey: activityQueryKey(''), queryFn: () => fetchActivity('') }],
}

/**
 * Pide los datos de una pantalla antes de abrirla.
 *
 * Se llama cuando el cursor pasa por la entrada del menu, cuando el teclado la
 * enfoca o cuando el dedo la toca: entre ese momento y el clic suele haber de
 * cien a trescientos milisegundos, y con eso la respuesta ya esta en cache al
 * llegar a la pantalla. `query` devuelve lo que ya esta en cache mientras siga
 * fresco, asi que pasar varias veces por la misma entrada no repite la peticion.
 */
export function prefetchRoute(queryClient: QueryClient, route: string): void {
  for (const consulta of CONSULTAS_POR_RUTA[route] ?? []) {
    // Un fallo de la precarga no se muestra: si la peticion falla de verdad,
    // la pantalla la repite al abrirse y ahi si presenta el error.
    queryClient.query(consulta).catch(() => undefined)
  }
}
