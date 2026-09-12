"""Puerto de lectura hacia `pets` y `medical_records`."""

from __future__ import annotations

from typing import Protocol

from gestvet.modules.insights.domain.entities import PetCareRecord

__all__ = ["ClinicalDirectory", "PetCareRecord"]


class ClinicalDirectory(Protocol):
    async def care_records(self) -> list[PetCareRecord]: ...
