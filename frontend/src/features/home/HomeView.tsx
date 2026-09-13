import { useSession } from '../../store/session'
import HomeHero from './HomeHero'
import HomeModules from './HomeModules'

export default function HomeView() {
  const user = useSession((state) => state.user)

  return (
    <div className="flex flex-col gap-16 pb-4">
      <HomeHero bleed={user === null} />
      <div className="mx-auto w-full max-w-[1100px]">
        <HomeModules />
      </div>
    </div>
  )
}
