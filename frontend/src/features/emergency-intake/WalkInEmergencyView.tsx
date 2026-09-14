import PageHeader from '../../components/PageHeader'
import { Card, CardContent } from '../../components/ui/card'
import WalkInEmergencyForm from './WalkInEmergencyForm'

export default function WalkInEmergencyView() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Emergencia — cliente nuevo"
        description="Para cuando llega alguien sin cuenta con su mascota. Con nombre y DNI alcanza: el correo y los demás datos se completan después, con calma."
      />

      <Card className="py-5 shadow-sm">
        <CardContent className="px-5">
          <WalkInEmergencyForm />
        </CardContent>
      </Card>
    </div>
  )
}
