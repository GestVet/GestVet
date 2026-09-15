import type { ComponentProps, ComponentType } from 'react'
import { createBrowserRouter, Navigate, type RouteObject } from 'react-router'

import RolesView from '../features/access/RolesView'
import VerifyCardView from '../features/card-verification/VerifyCardView'
import AppointmentsView from '../features/appointments/AppointmentsView'
import BookingView from '../features/appointments/BookingView'
import ForgotPasswordView from '../features/auth/ForgotPasswordView'
import LoginView from '../features/auth/LoginView'
import ProfileView from '../features/auth/ProfileView'
import RegisterView from '../features/auth/RegisterView'
import ResetPasswordView from '../features/auth/ResetPasswordView'
import MyShiftsView from '../features/availability/MyShiftsView'
import RosterView from '../features/availability/RosterView'
import PaymentsReportView from '../features/billing/PaymentsReportView'
import ComplaintsView from '../features/complaints/ComplaintsView'
import ActivityView from '../features/directory/ActivityView'
import ClientsView from '../features/directory/ClientsView'
import StaffView from '../features/directory/StaffView'
import WalkInEmergencyView from '../features/emergency-intake/WalkInEmergencyView'
import HomeView from '../features/home/HomeView'
import InsightsView from '../features/insights/InsightsView'
import TermsView from '../features/legal/TermsView'
import DashboardView from '../features/panel/DashboardView'
import PetCatalogView from '../features/pet-catalog/PetCatalogView'
import ClinicOverviewView from '../features/clinic-overview/ClinicOverviewView'
import PetsView from '../features/pets/PetsView'
import AppShell from '../features/shell/AppShell'
import RequireSession from '../features/shell/RequireSession'

/**
 * Una pantalla que exige un permiso.
 *
 * Es una comodidad de la interfaz: la autorizacion de verdad la aplica el
 * servidor en cada peticion, y esta guarda solo evita mostrar una pantalla que
 * va a responder 403. El permiso es el mismo que muestra la entrada del menu.
 */
function conPermiso(
  path: string,
  Component: ComponentType,
  permission: NonNullable<ComponentProps<typeof RequireSession>['permission']>,
): RouteObject {
  return {
    element: <RequireSession permission={permission} />,
    children: [{ path, Component }],
  }
}

const router = createBrowserRouter(
  [
    {
      path: '/',
      Component: AppShell,
      children: [
        { index: true, Component: HomeView },
        { path: 'acceso', Component: LoginView },
        { path: 'registro', Component: RegisterView },
        { path: 'olvide-contrasena', Component: ForgotPasswordView },
        { path: 'restablecer-contrasena', Component: ResetPasswordView },
        { path: 'terminos', Component: TermsView },
        // Pública: la abre quien escanea el QR del carnet de vacunas.
        { path: 'carnet/:token', Component: VerifyCardView },
        {
          element: <RequireSession />,
          children: [
            { path: 'panel', Component: DashboardView },
            { path: 'perfil', Component: ProfileView },
          ],
        },
        conPermiso('citas', AppointmentsView, 'appointments.read'),
        conPermiso('mascotas', PetsView, 'pets.manage_own'),
        conPermiso('reservar', BookingView, 'appointments.book'),
        conPermiso('agenda', MyShiftsView, 'schedule.read_own'),
        conPermiso('clientes', ClientsView, 'clients.read'),
        conPermiso('emergencia-cliente-nuevo', WalkInEmergencyView, 'emergencies.open_walk_in'),
        conPermiso('personal', StaffView, 'staff.read'),
        conPermiso('turnos', RosterView, 'schedule.manage'),
        conPermiso('roles', RolesView, 'roles.manage'),
        conPermiso('especies-y-razas', PetCatalogView, 'pets.manage_catalog'),
        conPermiso('pagos', PaymentsReportView, 'payments.report'),
        conPermiso('reclamos', ComplaintsView, 'complaints.read'),
        conPermiso('indicadores', InsightsView, 'insights.read'),
        conPermiso('panorama-clinica', ClinicOverviewView, [
          'pets.overview_read',
          'payments.report',
        ]),
        conPermiso('movimientos', ActivityView, 'activity.read'),
        // Cualquier ruta que no exista lleva a la landing, no a un error.
        { path: '*', element: <Navigate to="/" replace /> },
      ],
    },
  ],
  {
    basename: import.meta.env.BASE_URL,
  },
)

export default router
