from __future__ import annotations

from dataclasses import dataclass

from gestvet.core.activity import ActivityKind, ActivityRecorder
from gestvet.core.identity_registry import IdentityRegistry, IdentityRegistryUnavailable
from gestvet.modules.accounts.domain.entities import Role, User, ensure_role_is_self_assignable
from gestvet.modules.accounts.domain.exceptions import (
    DocumentIdRequired,
    DocumentNotFoundInRegistry,
    EmailAlreadyRegistered,
    IdentityCheckConsentRequired,
    IdentityMismatch,
    TermsNotAccepted,
)
from gestvet.modules.accounts.domain.identity_match import names_match
from gestvet.modules.accounts.ports.user_repository import PasswordHasher, UserRepository


@dataclass(frozen=True, slots=True)
class RegisterClientCommand:
    email: str
    password: str
    first_name: str
    last_name: str
    document_id: str
    phone: str = ""
    # La persona autorizó verificar su DNI. Sin eso no se consulta ni se registra.
    accepts_identity_check: bool = False
    # La persona aceptó los términos y condiciones. Sin eso no se crea la cuenta.
    accepts_terms: bool = False


class RegisterClient:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        activity: ActivityRecorder,
        identity: IdentityRegistry,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._activity = activity
        self._identity = identity

    async def __call__(self, command: RegisterClientCommand) -> User:
        # El rol se fija aquí, en el servidor. Nunca llega desde el cliente.
        role = Role.CLIENT
        ensure_role_is_self_assignable(role)

        if not command.document_id.strip():
            raise DocumentIdRequired()
        if not command.accepts_terms:
            raise TermsNotAccepted()
        if not command.accepts_identity_check:
            raise IdentityCheckConsentRequired()

        candidate = User(
            email=command.email,
            first_name=command.first_name.strip(),
            last_name=command.last_name.strip(),
            phone=command.phone.strip(),
            document_id=command.document_id.strip(),
            role=role,
            password_hash=self._hasher.hash(command.password),
        )

        if await self._users.exists_with_email(candidate.email):
            raise EmailAlreadyRegistered(candidate.email)
        # Al final, cuando todo lo demás es válido: cada consulta al registro cuesta.
        await self._verify_identity(candidate)

        creado = await self._users.add(candidate)
        await self._activity.record(creado.id or 0, ActivityKind.CLIENT_REGISTERED)
        return creado

    async def _verify_identity(self, candidate: User) -> None:
        """El nombre escrito corresponde al DNI.

        Nunca devuelve el nombre registrado: el formulario es público y así no
        sirve para averiguar a quién pertenece un DNI.
        """
        try:
            registered = await self._identity.lookup(candidate.document_id)
        except IdentityRegistryUnavailable:
            # Sin proveedor configurado, o con el proveedor caído, el registro
            # sigue: verificar protege contra suplantaciones, pero nadie debería
            # quedarse sin cuenta porque un servicio externo no respondió.
            return
        if registered is None:
            raise DocumentNotFoundInRegistry()
        if not names_match(candidate.first_name, candidate.last_name, registered):
            raise IdentityMismatch()
