import 'sienna-accessibility'

/**
 * Widget de accesibilidad Sienna (MIT, github.com/bennyluk/Sienna-Accessibility-Widget).
 *
 * El paquete se auto-inicializa como side-effect al importarse y corre en el
 * navegador del visitante, sin cuenta ni variable de entorno a diferencia de
 * UserWay. Sí hace una llamada externa: publica el locale de cada idioma y la
 * fuente de lectura en cdn.jsdelivr.net y los descarga de ahí (el tarball los
 * trae, pero el paquete arma las URL contra el CDN). Aceptamos ese CDN; si
 * está bloqueado, el widget cae al inglés. Al definir una CSP hay que permitir
 * `connect-src` y `font-src https://cdn.jsdelivr.net` y `style-src
 * 'unsafe-inline'` (inyecta su hoja de estilos en el documento).
 */
export default function AccessibilityWidget() {
  return null
}
