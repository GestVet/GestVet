"""Cableado del adaptador HTTP de cuentas.

Solo provee lo que este módulo posee: el repositorio de usuarios y el cifrado
de contraseñas. La identidad de quien hace la petición la resuelve
`gestvet.core.auth`, que es compartido, para que ningún módulo tenga que
importar a otro con tal de saber quién está del otro lado.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from gestvet.core.auth import SessionDep
from gestvet.core.dni_factiliza import get_identity_registry
from gestvet.core.email import ConsoleEmailSender
from gestvet.core.identity_registry import IdentityRegistry
from gestvet.core.security import BcryptPasswordHasher
from gestvet.modules.accounts.adapters.persistence.directories import (
    SqlReviewsDirectory,
)
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_layout_repository import (
    SqlAlchemyLayoutRepository,
)
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_password_reset_repository import (
    SqlAlchemyPasswordResetRepository,
)
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.ports.email_sender import EmailSender
from gestvet.modules.accounts.ports.layout_repository import LayoutRepository
from gestvet.modules.accounts.ports.password_reset_repository import PasswordResetRepository
from gestvet.modules.accounts.ports.reviews_directory import ReviewsDirectory
from gestvet.modules.accounts.ports.user_repository import PasswordHasher, UserRepository


def get_user_repository(session: SessionDep) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


def get_password_reset_repository(session: SessionDep) -> PasswordResetRepository:
    return SqlAlchemyPasswordResetRepository(session)


def get_layout_repository(session: SessionDep) -> LayoutRepository:
    return SqlAlchemyLayoutRepository(session)


def get_email_sender() -> EmailSender:
    return ConsoleEmailSender()


def get_reviews_directory(session: SessionDep) -> ReviewsDirectory:
    return SqlReviewsDirectory(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]
PasswordResetRepositoryDep = Annotated[
    PasswordResetRepository, Depends(get_password_reset_repository)
]
LayoutRepositoryDep = Annotated[LayoutRepository, Depends(get_layout_repository)]
EmailSenderDep = Annotated[EmailSender, Depends(get_email_sender)]
ReviewsDirectoryDep = Annotated[ReviewsDirectory, Depends(get_reviews_directory)]
IdentityRegistryDep = Annotated[IdentityRegistry, Depends(get_identity_registry)]
