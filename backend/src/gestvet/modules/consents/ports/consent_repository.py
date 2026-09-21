"""Puerto de persistencia de consentimientos y de sus textos."""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.consents.domain.entities import Consent, ConsentKind, ConsentTemplate


class ConsentTemplateRepository(Protocol):
    async def get(self, template_id: int) -> ConsentTemplate | None: ...

    async def current(self, kind: ConsentKind) -> ConsentTemplate | None:
        """La versión activa más alta del tipo: la que se muestra para firmar."""
        ...


class ConsentRepository(Protocol):
    async def add(self, consent: Consent) -> Consent: ...

    async def get(self, consent_id: int) -> Consent | None: ...

    async def update(self, consent: Consent) -> Consent:
        """Guarda la respuesta a un pedido. El texto y su huella no cambian nunca."""
        ...

    async def list_for_appointment(self, appointment_id: int) -> list[Consent]:
        """Los de una cita, del más nuevo al más viejo."""
        ...

    async def list_for_client(self, client_id: int) -> list[Consent]:
        """Los pedidos que un veterinario le hizo al cliente, del más nuevo al más viejo."""
        ...
