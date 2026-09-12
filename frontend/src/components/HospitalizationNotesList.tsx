const FORMATO = new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeStyle: 'short' })

interface NoteLike {
  readonly id: number
  readonly note: string
  readonly created_at: string
}

interface HospitalizationNotesListProps {
  readonly notes: readonly NoteLike[]
}

export default function HospitalizationNotesList({ notes }: HospitalizationNotesListProps) {
  if (notes.length === 0) {
    return <p className="empty">Todavía no hay notas de seguimiento.</p>
  }
  return (
    <ul className="stack">
      {notes.map((item) => (
        <li key={item.id}>
          <strong>{FORMATO.format(new Date(item.created_at))}:</strong> {item.note}
        </li>
      ))}
    </ul>
  )
}
