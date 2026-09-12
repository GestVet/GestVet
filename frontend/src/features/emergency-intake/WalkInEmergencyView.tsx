import WalkInEmergencyForm from './WalkInEmergencyForm'

export default function WalkInEmergencyView() {
  return (
    <div className="stack">
      <div className="page-header">
        <div>
          <h1>Emergencia — cliente nuevo</h1>
          <p className="muted">
            Para cuando llega alguien sin cuenta con su mascota. Con nombre y DNI alcanza: el
            correo y los demás datos se completan después, con calma.
          </p>
        </div>
      </div>

      <section className="card">
        <WalkInEmergencyForm />
      </section>
    </div>
  )
}
