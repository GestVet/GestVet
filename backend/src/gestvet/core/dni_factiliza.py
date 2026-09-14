"""Adaptador de consulta de DNI con Factiliza.

`GET {base}/dni/info/{dni}` con token Bearer. La respuesta trae, además de los
nombres, dirección y ubigeo: acá se descartan en el momento y nunca llegan al
resto del sistema ni a los logs.

Factiliza es un proveedor privado. Para producción conviene el convenio con
RENIEC; ver `README.md`, sección "Verificación de DNI".
"""

from __future__ import annotations

from typing import Any

import httpx

from gestvet.core.config import get_settings
from gestvet.core.identity_registry import (
    DisabledIdentityRegistry,
    IdentityRegistry,
    IdentityRegistryUnavailable,
    PersonName,
)
from gestvet.core.logs import get_logger

logger = get_logger("gestvet.identity")

_NOT_FOUND = 404
_VISIBLE_DIGITS = 3


def _masked(document_id: str) -> str:
    return f"***{document_id[-_VISIBLE_DIGITS:]}"


def _pretty(value: object) -> str:
    # El padrón viene en mayúsculas: "JOSE PEDRO" se muestra "Jose Pedro".
    return " ".join(str(value or "").split()).title()


class FactilizaIdentityRegistry:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        # Las pruebas pasan un transporte falso: ninguna consulta un DNI real.
        self._transport = transport

    async def lookup(self, document_id: str) -> PersonName | None:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.get(
                    f"{self._base_url}/dni/info/{document_id}",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
            if response.status_code == _NOT_FOUND:
                return None
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as error:
            logger.warning("identity.lookup_failed", dni=_masked(document_id), error=str(error))
            raise IdentityRegistryUnavailable(
                "No se pudo consultar el DNI en este momento. Inténtalo de nuevo."
            ) from error
        return _person(payload, document_id)


def _person(payload: dict[str, Any], document_id: str) -> PersonName | None:
    data = payload.get("data")
    if payload.get("success") is False or not isinstance(data, dict) or not data.get("nombres"):
        logger.info("identity.lookup_not_found", dni=_masked(document_id))
        return None
    logger.info("identity.lookup_found", dni=_masked(document_id))
    return PersonName(
        first_names=_pretty(data.get("nombres")),
        paternal_surname=_pretty(data.get("apellido_paterno")),
        maternal_surname=_pretty(data.get("apellido_materno")),
    )


def get_identity_registry() -> IdentityRegistry:
    settings = get_settings()
    if not settings.factiliza_api_key:
        return DisabledIdentityRegistry()
    return FactilizaIdentityRegistry(
        api_key=settings.factiliza_api_key,
        base_url=settings.factiliza_base_url,
        timeout_seconds=settings.identity_registry_timeout_seconds,
    )
