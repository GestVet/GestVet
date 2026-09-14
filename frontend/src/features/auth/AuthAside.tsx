import Icon from '../../components/Icon'
import type { IconName } from '../../components/icons'

export interface AuthAsideItem {
  readonly icon: IconName
  readonly text: string
}

interface AuthAsideProps {
  readonly title: string
  readonly items: readonly AuthAsideItem[]
  /** Una aclaracion al pie: quien entra por aca y para que se pide un dato. */
  readonly note: string
}

/**
 * El panel azul de las pantallas de acceso.
 *
 * Cuenta que se puede hacer con la cuenta usando solo funciones que existen.
 * Es el unico bloque de color intenso de la pantalla, asi el formulario queda
 * tranquilo al lado.
 */
export default function AuthAside({ title, items, note }: AuthAsideProps) {
  return (
    <aside className="flex flex-col gap-8 rounded-xl bg-primary p-6 text-primary-foreground sm:p-8">
      <div className="flex flex-col gap-6">
        <h2 className="m-0 font-heading text-2xl leading-tight font-bold text-balance">{title}</h2>
        <ul className="m-0 flex list-none flex-col gap-4 p-0">
          {items.map((item) => (
            <li key={item.text} className="flex items-start gap-3 text-base leading-relaxed">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-white/10">
                <Icon name={item.icon} size={20} />
              </span>
              <span className="pt-1.5">{item.text}</span>
            </li>
          ))}
        </ul>
      </div>
      <p className="m-0 border-t border-white/20 pt-5 text-sm leading-relaxed text-primary-foreground/85">
        {note}
      </p>
    </aside>
  )
}
