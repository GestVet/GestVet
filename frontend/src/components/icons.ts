// Registro de iconos. Unica fuente de verdad de toda la interfaz.
//
// Cada nombre del dominio apunta a un icono de Lucide, la biblioteca que trae
// shadcn/ui. Cambiar el icono de "citas" por otro es editar una linea de este
// archivo y verlo en todas las pantallas, sin tocar ni un componente: el resto
// de la aplicacion no importa Lucide, pide un nombre a `Icon.tsx`.
//
// Todos comparten el mismo trazo y se dibujan con el color del texto que los
// rodea, para que hereden el tono de donde se usen.

import {
  Banknote,
  CalendarCheck2,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  ChartColumnIncreasing,
  Check,
  Circle,
  CircleAlert,
  CircleX,
  Clock,
  Download,
  Eye,
  EyeOff,
  FolderHeart,
  HeartPulse,
  House,
  LogIn,
  LogOut,
  type LucideIcon,
  Mail,
  MapPin,
  Menu,
  PawPrint,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  TriangleAlert,
  UserRound,
  UserRoundPlus,
} from 'lucide-react'

export const ICONS = {
  // Marca.
  huella: PawPrint,

  // Navegacion y dominio. Tres nombres comparten icono a proposito: lo que los
  // separa es el significado, no el dibujo.
  inicio: House,
  menu: Menu,
  mascota: PawPrint,
  agenda: CalendarDays,
  cita: CalendarCheck2,
  emergencia: TriangleAlert,
  personal: UserRound,
  cliente: UserRound,
  perfil: UserRound,
  ubicacion: MapPin,
  horario: Clock,

  // Acciones.
  agregar: Plus,
  confirmar: Check,
  cancelar: CircleX,
  salir: LogOut,
  entrar: LogIn,
  registrarse: UserRoundPlus,
  correo: Mail,
  ver: Eye,
  ocultar: EyeOff,
  buscar: Search,
  pago: Banknote,
  descargar: Download,
  anterior: ChevronLeft,
  siguiente: ChevronRight,

  // Estado.
  activo: Circle,
  alerta: CircleAlert,
  indicadores: ChartColumnIncreasing,
  salud: HeartPulse,
  carpeta: FolderHeart,
  engranaje: Settings,
  permisos: ShieldCheck,
} as const satisfies Record<string, LucideIcon>

export type IconName = keyof typeof ICONS
