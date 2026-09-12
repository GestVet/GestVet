// Registro de iconos. Unica fuente de verdad de toda la interfaz.
//
// Un icono es un dato y no un componente: su trazo vive aca y lo dibuja
// `Icon.tsx`. Esa separacion es la que hace que cambiar el icono de "citas"
// por otro sea editar una linea de este archivo y verlo en todas las
// pantallas, sin tocar ni un componente.
//
// Tambien es lo que permite que exista un unico componente de icono en lugar
// de sesenta, cada uno con su propio svg copiado y su propio tamano.
//
// Todos los trazos estan normalizados a una caja de 24 por 24 y se dibujan con
// el color del texto que los rodea, para que hereden el tono de donde se usen.

export const ICON_VIEWBOX = '0 0 24 24'

// Tres nombres distintos comparten trazo a proposito. Lo que los separa es el
// significado, no el dibujo: el dia que el perfil propio necesite un icono
// distinto del listado de clientes, se cambia una sola linea de aca abajo.
const SILUETA_PERSONA =
  'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm0 2c-4 0-8 2-8 4.5V21h16v-2.5c0-2.5-4-4.5-8-4.5z'

export const ICONS = {
  // Marca: la huella del sistema original.
  huella:
    'M12 13c1.657 0 3 1.343 3 3s-1.343 3-3 3-3-1.343-3-3 1.343-3 3-3zm-5.934-.346c.938 0 1.7.76 1.7 1.697 0 .938-.762 1.7-1.7 1.7s-1.7-.762-1.7-1.7c0-.937.762-1.697 1.7-1.697zm11.868 0c.938 0 1.7.76 1.7 1.697 0 .938-.762 1.7-1.7 1.7s-1.7-.762-1.7-1.7c0-.937.762-1.697 1.7-1.697zm-5.934-6.346c1.106 0 2 .894 2 2 0 1.104-.894 2-2 2s-2-.896-2-2c0-1.106.894-2 2-2zm-4.75 1.285c.963 0 1.75.785 1.75 1.75s-.787 1.75-1.75 1.75c-.964 0-1.75-.785-1.75-1.75s.786-1.75 1.75-1.75zm9.5 0c.963 0 1.75.785 1.75 1.75s-.787 1.75-1.75 1.75c-.964 0-1.75-.785-1.75-1.75s.786-1.75 1.75-1.75z',

  // Navegacion y dominio.
  inicio: 'M12 3 2 12h3v8h6v-6h2v6h6v-8h3z',
  mascota:
    'M4.5 9.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4zm5-2.5a2.2 2.2 0 1 0 0-4.4 2.2 2.2 0 0 0 0 4.4zm5 0a2.2 2.2 0 1 0 0-4.4 2.2 2.2 0 0 0 0 4.4zm5 2.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM12 10c-2.6 0-5.2 2.4-6.3 4.6-1 2 .2 4.4 2.5 4.4 1.1 0 2.3-.5 3.8-.5s2.7.5 3.8.5c2.3 0 3.5-2.4 2.5-4.4C17.2 12.4 14.6 10 12 10z',
  agenda:
    'M7 2v2H5.5A2.5 2.5 0 0 0 3 6.5v13A2.5 2.5 0 0 0 5.5 22h13a2.5 2.5 0 0 0 2.5-2.5v-13A2.5 2.5 0 0 0 18.5 4H17V2h-2v2H9V2H7zm12 8v9.5a.5.5 0 0 1-.5.5h-13a.5.5 0 0 1-.5-.5V10h14z',
  cita: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 5v5.4l4 2.4-.8 1.3-5.2-3.1V7h2z',
  emergencia:
    'M12 2 1 21h22L12 2zm1 14h-2v2h2v-2zm0-7h-2v5h2V9z',
  personal: SILUETA_PERSONA,
  cliente: SILUETA_PERSONA,
  perfil: SILUETA_PERSONA,

  // Acciones.
  agregar: 'M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6V5z',
  confirmar: 'm9.6 16.2-3.8-3.8L4.4 13.8l5.2 5.2L20 8.6l-1.4-1.4z',
  cancelar:
    'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm5 13.6L15.6 17 12 13.4 8.4 17 7 15.6 10.6 12 7 8.4 8.4 7 12 10.6 15.6 7 17 8.4 13.4 12 17 15.6z',
  salir: 'M10 3H5.5A2.5 2.5 0 0 0 3 5.5v13A2.5 2.5 0 0 0 5.5 21H10v-2H5V5h5V3zm6.2 4.6-1.4 1.4 2 2H9v2h7.8l-2 2 1.4 1.4L21 12l-4.8-4.4z',
  buscar:
    'M10 3a7 7 0 1 0 4.2 12.6l4.6 4.6 1.4-1.4-4.6-4.6A7 7 0 0 0 10 3zm0 2a5 5 0 1 1 0 10 5 5 0 0 1 0-10z',
  pago: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 15.9v1.1h-2v-1.1c-1.5-.3-2.6-1.2-2.8-2.7h1.8c.1.6.7 1.1 1.7 1.1.9 0 1.6-.4 1.6-1.1 0-.6-.5-.9-1.8-1.2-1.8-.4-3-1-3-2.6 0-1.3 1-2.2 2.5-2.5V7.7h2v1.1c1.4.3 2.3 1.2 2.5 2.5h-1.8c-.1-.6-.6-1-1.5-1-.8 0-1.4.4-1.4 1 0 .6.6.8 1.8 1.1 1.9.4 3 1.1 3 2.7 0 1.4-1.1 2.3-2.6 2.6z',

  // Estado.
  activo: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z',
  alerta:
    'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z',
} as const

export type IconName = keyof typeof ICONS
