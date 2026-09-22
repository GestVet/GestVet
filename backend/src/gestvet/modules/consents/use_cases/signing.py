"""Lo que comparte cualquier firma, sea en línea o en el mostrador."""

from __future__ import annotations

from dataclasses import dataclass

from gestvet.modules.consents.domain.entities import ConsentKind, ConsentTemplate
from gestvet.modules.consents.domain.exceptions import (
    PetNotOwned,
    TemplateNotFound,
    TemplateOutdated,
)
from gestvet.modules.consents.ports.consent_repository import ConsentTemplateRepository
from gestvet.modules.consents.ports.pet_directory import PetDirectory


@dataclass(frozen=True, slots=True)
class RequestOrigin:
    """Desde dónde se firmó. Lo completa el adaptador HTTP; el negocio solo lo guarda."""

    ip: str = ""
    user_agent: str = ""


async def template_to_sign(
    templates: ConsentTemplateRepository, template_id: int, kind: ConsentKind
) -> ConsentTemplate:
    """La plantilla que quien firma dice haber leído, si todavía es la vigente.

    Se exige el identificador y no se toma la vigente sin más: así queda
    registrado el texto que la persona tuvo delante, y si cambió en el medio
    se le pide que lo vuelva a leer en vez de atribuirle uno que no vio.
    """
    template = await templates.get(template_id)
    if template is None or template.kind is not kind:
        raise TemplateNotFound(template_id)
    current = await templates.current(kind)
    if not template.is_active or current is None or current.id != template.id:
        raise TemplateOutdated()
    return template


async def ensure_pet_of(pets: PetDirectory, pet_id: int, client_id: int) -> None:
    # Misma respuesta para "no existe" y "es de otro dueño": distinguirlas
    # confirmaría que el identificador pertenece a alguien.
    if not await pets.is_owned_by(pet_id, client_id):
        raise PetNotOwned(pet_id)
