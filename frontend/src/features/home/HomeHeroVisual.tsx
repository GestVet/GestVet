const ALT_HEROE =
  'Fotografía ilustrativa de un veterinario con una tablet. No representa al personal de la clínica.'

/**
 * La foto del heroe, sola. Antes llevaba encima una miniatura del sistema
 * armada con cajas: parecia una captura sin serlo.
 */
export default function HomeHeroVisual() {
  return (
    <img
      alt={ALT_HEROE}
      fetchPriority="high"
      decoding="async"
      className="h-72 w-full rounded-xl object-cover object-[78%_center] sm:h-[24rem] lg:h-[28rem]"
      height={1200}
      src="/landing/hero-veterinario.png"
      width={1600}
    />
  )
}
