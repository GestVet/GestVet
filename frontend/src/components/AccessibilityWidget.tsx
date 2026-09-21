import { useEffect } from 'react'
import 'sienna-accessibility'

const ETIQUETA_ESPANOL = 'Abrir menú de accesibilidad'
const ATRIBUTOS_ETIQUETA = ['aria-label', 'title'] as const

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
 *
 * Localización del botón:
 * En sienna-accessibility@2.2.333, la función Oe() crea el botón flotante
 * (`a.asw-menu-btn`) con `aria-label="Open Accessibility Menu"` y
 * `title="Open Accessibility Menu"` fijos en inglés, ignorando el idioma
 * del documento (`<html lang="es">`). Para garantizar WCAG 3.1.2 (idioma de las
 * partes) y WCAG 4.1.2 (nombre accesible correcto en lectores de pantalla),
 * este componente usa un MutationObserver acotado que localiza el botón a
 * 'Abrir menú de accesibilidad' tanto al montarse como ante cualquier
 * mutación del DOM.
 */
export default function AccessibilityWidget() {
  useEffect(() => {
    function parchearBoton(boton: Element) {
      // Solo escribe si cambió: así el propio parche no vuelve a disparar el observer.
      for (const atributo of ATRIBUTOS_ETIQUETA) {
        if (boton.getAttribute(atributo) !== ETIQUETA_ESPANOL) {
          boton.setAttribute(atributo, ETIQUETA_ESPANOL)
        }
      }
    }

    const existente = document.querySelector('.asw-menu-btn')
    if (existente) {
      parchearBoton(existente)
    }

    const contenedor = document.querySelector('.asw-container') ?? document.body
    const observer = new MutationObserver(() => {
      const boton = document.querySelector('.asw-menu-btn')
      if (boton) {
        parchearBoton(boton)
      }
    })

    observer.observe(contenedor, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: [...ATRIBUTOS_ETIQUETA],
    })

    return () => {
      observer.disconnect()
    }
  }, [])

  return null
}
