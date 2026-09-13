import HomeProductPreview from './HomeProductPreview'

const ALT_HEROE =
  'Fotografía ilustrativa de un veterinario con una tablet. No representa al personal de la clínica.'

export default function HomeHeroVisual() {
  return (
    <div className="relative">
      <img
        alt={ALT_HEROE}
        className="h-72 w-full rounded-xl object-cover object-[78%_center] sm:h-[24rem] lg:h-[28rem]"
        height={1200}
        src="/landing/hero-veterinario.png"
        width={1600}
      />
      <div className="absolute bottom-4 left-3 sm:bottom-8 sm:-left-6 lg:-left-10">
        <HomeProductPreview />
      </div>
    </div>
  )
}
