"""Adaptador de entrada HTTP para el acceso.

Traduce credenciales a un token y errores de dominio a códigos de estado. No
decide nada: la regla de quién puede entrar vive en el caso de uso.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from gestvet.core.activity_log import ActivityRecorderDep
from gestvet.core.auth import UNAUTHENTICATED_HEADERS, PrincipalDep, TokenServiceDep
from gestvet.core.config import get_settings
from gestvet.modules.accounts.adapters.api.dependencies import (
    EmailSenderDep,
    PasswordHasherDep,
    PasswordResetRepositoryDep,
    UserRepositoryDep,
)
from gestvet.modules.accounts.adapters.api.schemas import (
    AccessTokenResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterClientRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    UserResponse,
)
from gestvet.modules.accounts.domain.exceptions import (
    EmailAlreadyRegistered,
    InactiveAccount,
    InvalidCredentials,
    InvalidEmail,
    InvalidResetToken,
    UserNotFound,
)
from gestvet.modules.accounts.use_cases.authenticate_user import (
    AuthenticateUser,
    AuthenticateUserCommand,
)
from gestvet.modules.accounts.use_cases.manage_accounts import UpdateProfile, UpdateProfileCommand
from gestvet.modules.accounts.use_cases.register_client import RegisterClient, RegisterClientCommand
from gestvet.modules.accounts.use_cases.request_password_reset import (
    RequestPasswordReset,
    RequestPasswordResetCommand,
)
from gestvet.modules.accounts.use_cases.reset_password import ResetPassword, ResetPasswordCommand

router = APIRouter()

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
) -> UserResponse:
    use_case = RegisterClient(users, hasher, activity)
    try:
        user = await use_case(
            RegisterClientCommand(
                email=str(payload.email),
                password=payload.password,
                first_name=payload.first_name,
                last_name=payload.last_name,
                phone=payload.phone,
            )
        )
    except EmailAlreadyRegistered as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except InvalidEmail as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return UserResponse.from_entity(user)


@router.post("/login", response_model=AccessTokenResponse, summary="Obtener un token de acceso")
async def login(
    payload: LoginRequest,
    users: UserRepositoryDep,
    hasher: PasswordHasherDep,
    tokens: TokenServiceDep,
    activity: ActivityRecorderDep,
) -> AccessTokenResponse:
    use_case = AuthenticateUser(users, hasher, tokens, activity)
    try:
        session = await use_case(
            AuthenticateUserCommand(email=str(payload.email), password=payload.password)
        )
    except InvalidCredentials as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, str(error), headers=UNAUTHENTICATED_HEADERS
        ) from error
    except InactiveAccount as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error

    return AccessTokenResponse(
        access_token=session.token.value,
        expires_in=session.token.expires_in_seconds,
        user=UserResponse.from_entity(session.user),
    )


@router.get("/me", response_model=UserResponse, summary="Cuenta que emitió la petición")
async def read_current_user(principal: PrincipalDep, users: UserRepositoryDep) -> UserResponse:
    # El principal solo trae identificador y rol. El perfil completo lo posee
    # este módulo, así que acá sí se lee la entidad entera.
    user = await users.get(principal.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La cuenta ya no existe.")
    return UserResponse.from_entity(user)


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
                new_password=payload.new_password,
            )
        )
    except UserNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return UserResponse.from_entity(user)


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
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    return MessageResponse(message="Contraseña actualizada. Ya podés iniciar sesión.")
