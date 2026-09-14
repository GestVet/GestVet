import { cn } from 'cn'

import HomeHeroCopy from './HomeHeroCopy'
import HomeHeroVisual from './HomeHeroVisual'

interface HomeHeroProps {
  readonly bleed: boolean
}

/**
 * El primer plano de la landing: oferta a la izquierda, foto a la derecha.
 */
export default function HomeHero({ bleed }: HomeHeroProps) {
  return (
    <section
      className={cn(
        bleed ? '-mx-4 -mt-6 sm:-mx-6' : 'rounded-xl bg-card px-4 py-8 sm:px-8',
      )}
    >
      <div
        className={cn(
          'grid items-center gap-12 py-10 md:grid-cols-[1.25fr_1fr] md:gap-8 lg:gap-12',
          bleed && 'mx-auto max-w-[1100px] px-4 sm:px-6 sm:py-16',
        )}
      >
        <HomeHeroCopy />
        <HomeHeroVisual />
      </div>
    </section>
  )
}
