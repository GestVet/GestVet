import PageHeader from '../../components/PageHeader'
import SectionCard from '../../components/SectionCard'
import { useScrollToHash } from '../../hooks/useScrollToHash'

const ACTUALIZADO = '14 de septiembre de 2026'

/**
 * Términos y condiciones, y política de privacidad.
 *
 * Pública: se enlaza desde el pie de página y desde el registro, antes de
 * crear la cuenta. Texto provisional para el lanzamiento; se reemplaza por la
 * versión revisada por un abogado antes de operar con clientes reales.
 */
export default function TermsView() {
  // "Política de privacidad" llega como /terminos#privacidad: sin esto la
  // página queda arriba en vez de bajar a la sección 6.
  useScrollToHash()

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 py-8">
      <PageHeader
        title="Términos y condiciones"
        description={`Última actualización: ${ACTUALIZADO}.`}
      />

      <SectionCard title="1. Qué es GestVet">
        <p className="m-0 text-sm text-muted-foreground">
          GestVet es el sistema de gestión de la clínica veterinaria a través del cual reservas
          citas, consultas la historia clínica de tus mascotas, recibes recordatorios y realizas
          pagos. Al crear una cuenta aceptas estos términos y nuestra política de privacidad.
        </p>
      </SectionCard>

      <SectionCard title="2. Tu cuenta">
        <ul className="m-0 flex list-disc flex-col gap-1.5 pl-5 text-sm text-muted-foreground">
          <li>Eres responsable de mantener tu contraseña en secreto y de la actividad de tu cuenta.</li>
          <li>Los datos que registras (nombre, DNI, teléfono, mascotas) deben ser reales y tuyos.</li>
          <li>
            Verificamos tu DNI contra fuentes oficiales solo para confirmar tu identidad, con tu
            autorización expresa en el registro.
          </li>
          <li>Podemos suspender una cuenta si detectamos datos falsos o uso indebido del sistema.</li>
        </ul>
      </SectionCard>

      <SectionCard title="3. Citas, pagos y cancelaciones">
        <ul className="m-0 flex list-disc flex-col gap-1.5 pl-5 text-sm text-muted-foreground">
          <li>Reservar una cita no garantiza atención si no te presentas dentro del margen de tolerancia.</li>
          <li>
            Los pagos por QR se confirman de forma automática; ante cualquier discrepancia, contáctanos
            antes de disputar el cargo con tu entidad financiera.
          </li>
          <li>Las tarifas se muestran antes de confirmar cada servicio y pueden variar entre citas.</li>
        </ul>
      </SectionCard>

      <SectionCard title="4. Comunicaciones">
        <p className="m-0 text-sm text-muted-foreground">
          Usamos tu correo y, si lo registraste, tu WhatsApp para confirmaciones de cita, recordatorios
          de vacunas próximas y avisos de pago. Son notificaciones de servicio, no publicidad; no puedes
          desactivarlas por completo mientras tengas citas o tratamientos activos.
        </p>
      </SectionCard>

      <SectionCard title="5. Historia clínica">
        <p className="m-0 text-sm text-muted-foreground">
          La historia clínica de tu mascota (diagnósticos, tratamientos, vacunas, adjuntos) la registra
          el personal veterinario que te atiende. Tú puedes consultarla en cualquier momento desde tu
          cuenta; no la compartimos con terceros salvo que la ley lo exija o tú lo autorices (por ejemplo,
          al generar un carnet de vacunas verificable por QR).
        </p>
      </SectionCard>

      <div id="privacidad" className="scroll-mt-20">
        <SectionCard title="6. Privacidad de tus datos">
        <ul className="m-0 flex list-disc flex-col gap-1.5 pl-5 text-sm text-muted-foreground">
          <li>Usamos tus datos únicamente para operar la clínica: citas, historia clínica, pagos y notificaciones.</li>
          <li>No vendemos tus datos personales ni los de tu mascota a terceros.</li>
          <li>
            Compartimos el mínimo necesario con proveedores que nos ayudan a operar (verificación de
            identidad, pasarela de pagos, envío de WhatsApp), bajo sus propias políticas de protección de
            datos.
          </li>
          <li>Puedes pedir la corrección o eliminación de tus datos escribiéndonos por los canales de contacto.</li>
        </ul>
        </SectionCard>
      </div>

      <SectionCard title="7. Cambios a estos términos">
        <p className="m-0 text-sm text-muted-foreground">
          Podemos actualizar estos términos para reflejar cambios en el sistema o en la normativa
          aplicable. Si el cambio es significativo, lo avisamos por correo antes de que entre en vigor.
        </p>
      </SectionCard>
    </div>
  )
}
