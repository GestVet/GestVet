"""Adaptador de entrada HTTP para el acceso.

Traduce credenciales a un token y errores de dominio a códigos de estado. No
decide nada: la regla de quién puede entrar vive en el caso de uso.

También deja el rastro de seguridad del acceso en los logs: altas, ingresos,
ingresos fallidos y recuperación de contraseña. Vive acá y no en los casos de
uso porque escribir un log es tecnología, y el dominio no la conoce.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import (
    UNAUTHENTICATED_HEADERS,
    PrincipalDep,
    SessionDep,
    TokenServiceDep,
    load_access,
)
from gestvet.core.config import get_settings
from gestvet.core.logs import get_logger, mask_email
from gestvet.modules.accounts.adapters.api.dependencies import (
    EmailSenderDep,
    IdentityRegistryDep,
    LayoutRepositoryDep,
    PasswordHasherDep,
    PasswordResetRepositoryDep,
    UserRepositoryDep,
)
from gestvet.modules.accounts.adapters.api.schemas import (
    AccessTokenResponse,
    CurrentUserResponse,
    ForgotPasswordRequest,
    LayoutPreferencesRequest,
    LayoutPreferencesResponse,
    LoginRequest,
    MessageResponse,
    RegisterClientRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    UserResponse,
)
from gestvet.modules.accounts.domain.entities import DashboardBlockPreference, User
from gestvet.modules.accounts.domain.exceptions import (
    DocumentIdRequired,
    DocumentNotFoundInRegistry,
    EmailAlreadyRegistered,
    IdentityCheckConsentRequired,
    IdentityMismatch,
    InactiveAccount,
    InvalidCredentials,
    InvalidDocumentId,
    InvalidEmail,
    InvalidLayoutPreferences,
    InvalidResetToken,
    TermsNotAccepted,
    UserNotFound,
)
from gestvet.modules.accounts.use_cases.authenticate_user import (
    AuthenticateUser,
    AuthenticateUserCommand,
)
from gestvet.modules.accounts.use_cases.manage_accounts import UpdateProfile, UpdateProfileCommand
from gestvet.modules.accounts.use_cases.manage_layout import (
    GetLayoutPreferences,
    ResetLayoutPreferences,
    SaveLayoutPreferences,
    SaveLayoutPreferencesCommand,
)
from gestvet.modules.accounts.use_cases.register_client import RegisterClient, RegisterClientCommand
from gestvet.modules.accounts.use_cases.request_password_reset import (
    RequestPasswordReset,
    RequestPasswordResetCommand,
)
from gestvet.modules.accounts.use_cases.reset_password import ResetPassword, ResetPasswordCommand

router = APIRouter()
logger = get_logger("gestvet.auth")

# Misma respuesta exista o no la cuenta: si el mensaje cambiara con el
# resultado, cualquiera podría usar el formulario para averiguar qué correos
# están registrados.
FORGOT_PASSWORD_MESSAGE = "Si el correo está registrado, te enviamos instrucciones."


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Autorregistro de un cliente",
)
async def register_client(
    payload: RegisterClientRequest,
    users: UserRepositoryDep,
    hasher: PasswordHasherDep,
    activity: ActivityRecorderDep,
    identity: IdentityRegistryDep,
) -> UserResponse:
    use_case = RegisterClient(users, hasher, activity, identity)
    try:
        user = await use_case(
            RegisterClientCommand(
                email=str(payload.email),
                password=payload.password,
                first_name=payload.first_name,
                last_name=payload.last_name,
                document_id=payload.document_id,
                phone=payload.phone,
                accepts_identity_check=payload.accepts_identity_check,
                accepts_terms=payload.accepts_terms,
            )
        )
    except EmailAlreadyRegistered as error:
        logger.info("auth.register_rejected", reason="email_taken")
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except (
        InvalidEmail,
        InvalidDocumentId,
        DocumentIdRequired,
        TermsNotAccepted,
        IdentityCheckConsentRequired,
        DocumentNotFoundInRegistry,
        IdentityMismatch,
    ) as error:
        logger.info("auth.register_rejected", reason=type(error).__name__)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    logger.info("auth.registered", user_id=user.id, role=user.role.value)
    return UserResponse.from_entity(user)


@router.post("/login", response_model=AccessTokenResponse, summary="Obtener un token de acceso")
async def login(
    payload: LoginRequest,
    users: UserRepositoryDep,
    hasher: PasswordHasherDep,
    tokens: TokenServiceDep,
    activity: ActivityRecorderDep,
    db: SessionDep,
) -> AccessTokenResponse:
    use_case = AuthenticateUser(users, hasher, tokens, activity)
    try:
        session = await use_case(
            AuthenticateUserCommand(email=str(payload.email), password=payload.password)
        )
    except InvalidCredentials as error:
        # Aviso y no información: varios seguidos contra la misma cuenta son
        # la señal de un intento de adivinar la contraseña.
        logger.warning(
            "auth.login_failed", reason="invalid_credentials", email=mask_email(str(payload.email))
        )
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, str(error), headers=UNAUTHENTICATED_HEADERS
        ) from error
    except InactiveAccount as error:
        logger.warning(
            "auth.login_failed", reason="inactive_account", email=mask_email(str(payload.email))
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error

    logger.info("auth.login_succeeded", user_id=session.user.id, role=session.user.role.value)
    return AccessTokenResponse(
        access_token=session.token.value,
        expires_in=session.token.expires_in_seconds,
        user=await _with_access(db, session.user),
    )


async def _with_access(db: AsyncSession, user: User) -> CurrentUserResponse:
    access = await load_access(db, user.id or 0)
    return CurrentUserResponse.with_access(
        user, access.role_id, access.role_name, access.permissions
    )


@router.get("/me", response_model=CurrentUserResponse, summary="Cuenta que emitió la petición")
async def read_current_user(
    principal: PrincipalDep, users: UserRepositoryDep, db: SessionDep
) -> CurrentUserResponse:
    # El principal solo trae identificador, rol y permisos. El perfil completo
    # lo posee este módulo, así que acá sí se lee la entidad entera.
    user = await users.get(principal.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La cuenta ya no existe.")
    return await _with_access(db, user)


@router.patch("/me", response_model=UserResponse, summary="Editar el perfil propio")
async def update_current_user(
    payload: UpdateProfileRequest,
    principal: PrincipalDep,
    users: UserRepositoryDep,
    hasher: PasswordHasherDep,
    activity: ActivityRecorderDep,
) -> UserResponse:
    # No entran ni el correo ni el rol: el correo es la identidad con la que se
    # accede y el rol lo fija el servidor.
    try:
        user = await UpdateProfile(users, hasher, activity)(
            UpdateProfileCommand(
                user_id=principal.user_id,
                first_name=payload.first_name,
                last_name=payload.last_name,
                phone=payload.phone,
                document_id=payload.document_id,
                new_password=payload.new_password,
            )
        )
    except UserNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except InvalidDocumentId as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    if payload.new_password is not None:
        logger.info("auth.password_changed", user_id=principal.user_id)
    return UserResponse.from_entity(user)


@router.get(
    "/me/layout",
    response_model=LayoutPreferencesResponse,
    summary="Preferencias de orden del sidebar y bloques del panel principal",
)
async def read_my_layout(
    principal: PrincipalDep,
    layout_repo: LayoutRepositoryDep,
) -> LayoutPreferencesResponse:
    use_case = GetLayoutPreferences(layout_repo)
    preferences = await use_case(principal.user_id)
    return LayoutPreferencesResponse.from_entity(preferences)


@router.put(
    "/me/layout",
    response_model=LayoutPreferencesResponse,
    summary="Guardar o actualizar preferencias de interfaz",
)
async def update_my_layout(
    payload: LayoutPreferencesRequest,
    principal: PrincipalDep,
    layout_repo: LayoutRepositoryDep,
) -> LayoutPreferencesResponse:
    use_case = SaveLayoutPreferences(layout_repo)
    try:
        preferences = await use_case(
            SaveLayoutPreferencesCommand(
                user_id=principal.user_id,
                sidebar_order=payload.sidebar_order,
                dashboard_blocks=[
                    DashboardBlockPreference(id=b.id, visible=b.visible)
                    for b in payload.dashboard_blocks
                ],
            )
        )
    except InvalidLayoutPreferences as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return LayoutPreferencesResponse.from_entity(preferences)


@router.delete(
    "/me/layout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Restablecer preferencias de interfaz a los valores por defecto",
)
async def reset_my_layout(
    principal: PrincipalDep,
    layout_repo: LayoutRepositoryDep,
) -> Response:
    use_case = ResetLayoutPreferences(layout_repo)
    await use_case(principal.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Pedir un enlace de recuperación de contraseña",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    users: UserRepositoryDep,
    tokens: PasswordResetRepositoryDep,
    email_sender: EmailSenderDep,
) -> MessageResponse:
    use_case = RequestPasswordReset(users, tokens, email_sender, get_settings().frontend_base_url)
    await use_case(RequestPasswordResetCommand(email=str(payload.email)))
    logger.info("auth.password_reset_requested", email=mask_email(str(payload.email)))
    return MessageResponse(message=FORGOT_PASSWORD_MESSAGE)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Fijar una contraseña nueva con el enlace recibido",
)
async def reset_password(
    payload: ResetPasswordRequest,
    users: UserRepositoryDep,
    tokens: PasswordResetRepositoryDep,
    hasher: PasswordHasherDep,
) -> MessageResponse:
    try:
        await ResetPassword(users, tokens, hasher)(
            ResetPasswordCommand(token=payload.token, new_password=payload.new_password)
        )
    except InvalidResetToken as error:
        logger.warning("auth.password_reset_rejected", reason="invalid_token")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    logger.info("auth.password_reset_completed")
    return MessageResponse(message="Contraseña actualizada. Ya puedes iniciar sesión.")
