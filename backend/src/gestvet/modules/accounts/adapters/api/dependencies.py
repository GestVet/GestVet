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
from gestvet.core.security import BcryptPasswordHasher
from gestvet.modules.accounts.adapters.persistence.directories import SqlAppointmentDirectory
from gestvet.modules.accounts.adapters.persistence.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from gestvet.modules.accounts.ports.appointment_directory import AppointmentDirectory
from gestvet.modules.accounts.ports.user_repository import PasswordHasher, UserRepository


def get_user_repository(session: SessionDep) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


def get_appointment_directory(session: SessionDep) -> AppointmentDirectory:
    return SqlAppointmentDirectory(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]
AppointmentDirectoryDep = Annotated[AppointmentDirectory, Depends(get_appointment_directory)]
