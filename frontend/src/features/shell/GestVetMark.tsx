import { useId } from 'react'

interface GestVetMarkProps {
  readonly size?: number
}

/**
 * La huella con corazon de la marca, en el azul de la aplicacion.
 */
export default function GestVetMark({ size = 36 }: GestVetMarkProps) {
  const rawId = useId()
  const gradientId = `gv-mark-${rawId.replaceAll(':', '')}`

  return (
    <svg
      aria-hidden="true"
      focusable="false"
      height={size}
      viewBox="0 0 64 64"
      width={size}
    >
      <defs>
        <linearGradient
          gradientUnits="userSpaceOnUse"
          id={gradientId}
          x1="12"
          x2="52"
          y1="4"
          y2="60"
        >
          <stop offset="0%" style={{ stopColor: 'var(--ring)' }} />
          <stop offset="100%" style={{ stopColor: 'var(--primary)' }} />
        </linearGradient>
      </defs>
      <g fill={`url(#${gradientId})`}>
        <circle cx="32" cy="10" r="5.2" />
        <circle cx="19" cy="15" r="4.8" />
        <circle cx="45" cy="15" r="4.8" />
        <circle cx="12" cy="26" r="4.4" />
        <circle cx="52" cy="26" r="4.4" />
        <path d="M32 58C21 49 14 42 14 34c0-5.2 4.2-9 9.2-9 2.8 0 5.2 1.3 8.8 5.2C35.6 26.3 38 25 40.8 25c5 0 9.2 3.8 9.2 9 0 8-7 15-18 24z" />
      </g>
    </svg>
  )
}
