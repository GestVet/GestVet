import { useScrollToHash } from '../../hooks/useScrollToHash'
import { useSession } from '../../store/session'
import HomeHero from './HomeHero'
import HomeModules from './HomeModules'
import HomeSteps from './HomeSteps'

export default function HomeView() {
  const user = useSession((state) => state.user)
  useScrollToHash()

  return (
    <div className="flex flex-col gap-16 pb-4">
      <HomeHero bleed={user === null} />
      <div className="mx-auto flex w-full max-w-[1100px] flex-col gap-16">
        <HomeModules />
        {user === null ? <HomeSteps /> : null}
      </div>
    </div>
  )
}
