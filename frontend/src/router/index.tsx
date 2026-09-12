import { createBrowserRouter } from 'react-router'

import AppointmentsView from '../features/appointments/AppointmentsView'
import BookingView from '../features/appointments/BookingView'
import ForgotPasswordView from '../features/auth/ForgotPasswordView'
import LoginView from '../features/auth/LoginView'
import ProfileView from '../features/auth/ProfileView'
import RegisterView from '../features/auth/RegisterView'
import ResetPasswordView from '../features/auth/ResetPasswordView'
import AvailabilityView from '../features/availability/AvailabilityView'
import PaymentsReportView from '../features/billing/PaymentsReportView'
import ActivityView from '../features/directory/ActivityView'
import ClientsView from '../features/directory/ClientsView'
import StaffView from '../features/directory/StaffView'
import HomeView from '../features/home/HomeView'
import DashboardView from '../features/panel/DashboardView'
import PetsView from '../features/pets/PetsView'
import AppShell from '../features/shell/AppShell'
import RequireSession from '../features/shell/RequireSession'

const CLIENTE = ['client'] as const
const VETERINARIOS = ['veterinarian', 'emergency_veterinarian'] as const
const PERSONAL = ['admin', 'veterinarian', 'emergency_veterinarian'] as const
const ADMIN = ['admin'] as const

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
        {
          // Las rutas de abajo exigen sesión. Es una comodidad de la
          // interfaz: la autorización de verdad la aplica el servidor en cada
          // petición, y esta guarda solo evita mostrar una pantalla vacía.
          element: <RequireSession />,
          children: [
            { path: 'panel', Component: DashboardView },
            { path: 'perfil', Component: ProfileView },
            { path: 'citas', Component: AppointmentsView },
          ],
        },
        {
          element: <RequireSession roles={CLIENTE} />,
          children: [
            { path: 'mascotas', Component: PetsView },
            { path: 'reservar', Component: BookingView },
          ],
        },
        {
          element: <RequireSession roles={VETERINARIOS} />,
          children: [{ path: 'agenda', Component: AvailabilityView }],
        },
        {
          element: <RequireSession roles={PERSONAL} />,
          children: [{ path: 'clientes', Component: ClientsView }],
        },
        {
          element: <RequireSession roles={ADMIN} />,
          children: [
            { path: 'personal', Component: StaffView },
            { path: 'pagos', Component: PaymentsReportView },
            { path: 'movimientos', Component: ActivityView },
          ],
        },
      ],
    },
  ],
  {
    basename: import.meta.env.BASE_URL,
  },
)

export default router
