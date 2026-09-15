"""Catálogo de permisos.

Un permiso es una acción que el servidor sabe comprobar: cada endpoint exige
uno. La lista es fija y vive en el código, porque cada permiso nuevo necesita un
endpoint que lo exija; lo que la administración cambia en caliente es qué roles
tienen cuáles.

Cada permiso declara además qué tipos de cuenta pueden tenerlo. El tipo de
cuenta (cliente, veterinario, administración) sigue decidiendo qué datos son
"tuyos": reservar una cita solo tiene sentido para quien tiene mascotas, y
atender una solo para quien tiene agenda. Así un rol editado no puede dar un
permiso que el dominio no sabría respetar.

Python puro: lo importa también el dominio del módulo de accesos.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from gestvet.core.identity import STAFF_ROLES, VETERINARIAN_ROLES, Role


class Permission(StrEnum):
    PETS_MANAGE_OWN = "pets.manage_own"
    PETS_REGISTER_FOR_OWNER = "pets.register_for_owner"
    PETS_READ_ANY = "pets.read_any"
    PETS_CORRECT_STATUS = "pets.correct_status"
    PETS_EDIT_CLINICAL_PROFILE = "pets.edit_clinical_profile"
    PETS_MANAGE_CATALOG = "pets.manage_catalog"
    PETS_OVERVIEW_READ = "pets.overview_read"
    APPOINTMENTS_READ = "appointments.read"
    APPOINTMENTS_BOOK = "appointments.book"
    APPOINTMENTS_ATTEND = "appointments.attend"
    APPOINTMENTS_CANCEL = "appointments.cancel"
    EMERGENCIES_OPEN = "emergencies.open"
    EMERGENCIES_OPEN_WALK_IN = "emergencies.open_walk_in"
    SCHEDULE_READ = "schedule.read"
    SCHEDULE_READ_OWN = "schedule.read_own"
    SCHEDULE_REQUEST_CHANGE = "schedule.request_change"
    SCHEDULE_MANAGE = "schedule.manage"
    VETERINARIANS_READ = "veterinarians.read"
    CLINICAL_RECORDS_READ = "clinical_records.read"
    CLINICAL_RECORDS_WRITE = "clinical_records.write"
    HOSPITALIZATIONS_READ = "hospitalizations.read"
    HOSPITALIZATIONS_MANAGE = "hospitalizations.manage"
    PAYMENTS_READ = "payments.read"
    PAYMENTS_QR = "payments.qr"
    PAYMENTS_REGISTER = "payments.register"
    PAYMENTS_VOID = "payments.void"
    PAYMENTS_REPORT = "payments.report"
    COMPLAINTS_READ = "complaints.read"
    COMPLAINTS_FILE = "complaints.file"
    REVIEWS_READ = "reviews.read"
    REVIEWS_SUBMIT = "reviews.submit"
    CLIENTS_READ = "clients.read"
    CLIENTS_REGISTER_WALK_IN = "clients.register_walk_in"
    CLIENTS_UPDATE_CONTACT = "clients.update_contact"
    STAFF_READ = "staff.read"
    STAFF_MANAGE = "staff.manage"
    USERS_CHANGE_STATUS = "users.change_status"
    ACTIVITY_READ = "activity.read"
    INSIGHTS_READ = "insights.read"
    ROLES_MANAGE = "roles.manage"


@dataclass(frozen=True, slots=True)
class PermissionInfo:
    label: str
    group: str
    account_kinds: frozenset[Role]


ALL_KINDS: frozenset[Role] = frozenset(Role)
CLIENT_KIND: frozenset[Role] = frozenset({Role.CLIENT})
ADMIN_KIND: frozenset[Role] = frozenset({Role.ADMIN})

_MASCOTAS = "Mascotas"
_CITAS = "Citas y emergencias"
_AGENDA = "Agenda"
_CLINICA = "Historia clínica e internación"
_PAGOS = "Pagos"
_OPINION = "Reclamos y reseñas"
_CLIENTES = "Clientes"
_ADMINISTRACION = "Administración"

# El orden en que la pantalla de roles muestra los grupos.
PERMISSION_GROUPS: tuple[str, ...] = (
    _MASCOTAS,
    _CITAS,
    _AGENDA,
    _CLINICA,
    _PAGOS,
    _OPINION,
    _CLIENTES,
    _ADMINISTRACION,
)

CATALOG: dict[Permission, PermissionInfo] = {
    Permission.PETS_MANAGE_OWN: PermissionInfo(
        "Registrar y editar sus propias mascotas", _MASCOTAS, CLIENT_KIND
    ),
    Permission.PETS_REGISTER_FOR_OWNER: PermissionInfo(
        "Registrar mascotas a nombre de un cliente", _MASCOTAS, STAFF_ROLES
    ),
    Permission.PETS_READ_ANY: PermissionInfo(
        "Ver las mascotas de cualquier cliente", _MASCOTAS, STAFF_ROLES
    ),
    Permission.PETS_CORRECT_STATUS: PermissionInfo(
        "Corregir el estado de una mascota", _MASCOTAS, STAFF_ROLES
    ),
    Permission.PETS_EDIT_CLINICAL_PROFILE: PermissionInfo(
        "Editar los datos clínicos de una mascota", _MASCOTAS, VETERINARIAN_ROLES
    ),
    Permission.PETS_MANAGE_CATALOG: PermissionInfo(
        "Agregar y corregir especies y razas", _MASCOTAS, STAFF_ROLES
    ),
    Permission.PETS_OVERVIEW_READ: PermissionInfo(
        "Ver el panorama de mascotas de la clínica", _MASCOTAS, STAFF_ROLES
    ),
    Permission.APPOINTMENTS_READ: PermissionInfo("Ver citas", _CITAS, ALL_KINDS),
    Permission.APPOINTMENTS_BOOK: PermissionInfo("Reservar citas", _CITAS, CLIENT_KIND),
    Permission.APPOINTMENTS_ATTEND: PermissionInfo(
        "Confirmar, completar o marcar inasistencia", _CITAS, VETERINARIAN_ROLES
    ),
    Permission.APPOINTMENTS_CANCEL: PermissionInfo("Cancelar citas", _CITAS, ALL_KINDS),
    Permission.EMERGENCIES_OPEN: PermissionInfo(
        "Abrir una emergencia para sus mascotas", _CITAS, CLIENT_KIND
    ),
    Permission.EMERGENCIES_OPEN_WALK_IN: PermissionInfo(
        "Abrir una emergencia desde el mostrador", _CITAS, STAFF_ROLES
    ),
    Permission.SCHEDULE_READ: PermissionInfo(
        "Ver los turnos de los veterinarios", _AGENDA, ALL_KINDS
    ),
    Permission.SCHEDULE_READ_OWN: PermissionInfo(
        "Ver sus turnos y guardias", _AGENDA, VETERINARIAN_ROLES
    ),
    Permission.SCHEDULE_REQUEST_CHANGE: PermissionInfo(
        "Pedir cambios de turno", _AGENDA, VETERINARIAN_ROLES
    ),
    Permission.SCHEDULE_MANAGE: PermissionInfo(
        "Asignar turnos y guardias y responder pedidos", _AGENDA, ADMIN_KIND
    ),
    Permission.VETERINARIANS_READ: PermissionInfo(
        "Ver el listado de veterinarios", _AGENDA, ALL_KINDS
    ),
    Permission.CLINICAL_RECORDS_READ: PermissionInfo(
        "Ver la historia clínica y descargarla", _CLINICA, ALL_KINDS
    ),
    Permission.CLINICAL_RECORDS_WRITE: PermissionInfo(
        "Registrar en la historia clínica y adjuntar archivos", _CLINICA, VETERINARIAN_ROLES
    ),
    Permission.HOSPITALIZATIONS_READ: PermissionInfo("Ver internaciones", _CLINICA, ALL_KINDS),
    Permission.HOSPITALIZATIONS_MANAGE: PermissionInfo(
        "Abrir internaciones, anotar y dar de alta", _CLINICA, VETERINARIAN_ROLES
    ),
    Permission.PAYMENTS_READ: PermissionInfo("Ver pagos", _PAGOS, ALL_KINDS),
    Permission.PAYMENTS_QR: PermissionInfo("Pagar o cobrar con QR", _PAGOS, ALL_KINDS),
    Permission.PAYMENTS_REGISTER: PermissionInfo("Registrar pagos", _PAGOS, STAFF_ROLES),
    Permission.PAYMENTS_VOID: PermissionInfo("Anular pagos", _PAGOS, STAFF_ROLES),
    Permission.PAYMENTS_REPORT: PermissionInfo(
        "Ver el resumen de pagos por medio", _PAGOS, STAFF_ROLES
    ),
    Permission.COMPLAINTS_READ: PermissionInfo("Ver reclamos", _OPINION, ALL_KINDS),
    Permission.COMPLAINTS_FILE: PermissionInfo(
        "Presentar reclamos con evidencia", _OPINION, CLIENT_KIND
    ),
    Permission.REVIEWS_READ: PermissionInfo("Ver reseñas", _OPINION, ALL_KINDS),
    Permission.REVIEWS_SUBMIT: PermissionInfo("Dejar reseñas", _OPINION, CLIENT_KIND),
    Permission.CLIENTS_READ: PermissionInfo("Ver el padrón de clientes", _CLIENTES, STAFF_ROLES),
    Permission.CLIENTS_REGISTER_WALK_IN: PermissionInfo(
        "Dar de alta clientes en el mostrador", _CLIENTES, STAFF_ROLES
    ),
    Permission.CLIENTS_UPDATE_CONTACT: PermissionInfo(
        "Completar el contacto de un cliente", _CLIENTES, STAFF_ROLES
    ),
    Permission.STAFF_READ: PermissionInfo("Ver el personal", _ADMINISTRACION, STAFF_ROLES),
    Permission.STAFF_MANAGE: PermissionInfo("Dar de alta personal", _ADMINISTRACION, ADMIN_KIND),
    Permission.USERS_CHANGE_STATUS: PermissionInfo(
        "Activar y desactivar cuentas", _ADMINISTRACION, ADMIN_KIND
    ),
    Permission.ACTIVITY_READ: PermissionInfo(
        "Ver los movimientos de las cuentas", _ADMINISTRACION, STAFF_ROLES
    ),
    Permission.INSIGHTS_READ: PermissionInfo("Ver indicadores", _ADMINISTRACION, STAFF_ROLES),
    Permission.ROLES_MANAGE: PermissionInfo(
        "Administrar roles y permisos", _ADMINISTRACION, ADMIN_KIND
    ),
}

_COMMON = frozenset(
    {
        Permission.APPOINTMENTS_READ,
        Permission.APPOINTMENTS_CANCEL,
        Permission.SCHEDULE_READ,
        Permission.VETERINARIANS_READ,
        Permission.PAYMENTS_READ,
        Permission.PAYMENTS_QR,
        Permission.COMPLAINTS_READ,
        Permission.HOSPITALIZATIONS_READ,
        Permission.CLINICAL_RECORDS_READ,
        Permission.REVIEWS_READ,
    }
)
_DESK = frozenset(
    {
        Permission.PETS_REGISTER_FOR_OWNER,
        Permission.PETS_READ_ANY,
        Permission.PETS_CORRECT_STATUS,
        Permission.EMERGENCIES_OPEN_WALK_IN,
        Permission.PAYMENTS_REGISTER,
        Permission.PAYMENTS_VOID,
        Permission.CLIENTS_READ,
        Permission.CLIENTS_REGISTER_WALK_IN,
        Permission.CLIENTS_UPDATE_CONTACT,
    }
)
_VETERINARY = (
    _COMMON
    | _DESK
    | {
        Permission.APPOINTMENTS_ATTEND,
        Permission.SCHEDULE_READ_OWN,
        Permission.SCHEDULE_REQUEST_CHANGE,
        Permission.HOSPITALIZATIONS_MANAGE,
        Permission.CLINICAL_RECORDS_WRITE,
        Permission.PETS_EDIT_CLINICAL_PROFILE,
        Permission.PETS_OVERVIEW_READ,
    }
)

# Los permisos de cada rol de sistema. Reproducen el acceso que la aplicación
# daba antes de existir los roles editables, así que una cuenta sin rol asignado
# se comporta igual que siempre.
SYSTEM_ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.CLIENT: _COMMON
    | {
        Permission.PETS_MANAGE_OWN,
        Permission.APPOINTMENTS_BOOK,
        Permission.EMERGENCIES_OPEN,
        Permission.COMPLAINTS_FILE,
        Permission.REVIEWS_SUBMIT,
    },
    Role.VETERINARIAN: _VETERINARY,
    Role.ADMIN: _COMMON
    | _DESK
    | {
        Permission.PAYMENTS_REPORT,
        Permission.STAFF_READ,
        Permission.STAFF_MANAGE,
        Permission.SCHEDULE_MANAGE,
        Permission.USERS_CHANGE_STATUS,
        Permission.ACTIVITY_READ,
        Permission.INSIGHTS_READ,
        Permission.ROLES_MANAGE,
        Permission.PETS_MANAGE_CATALOG,
        Permission.PETS_OVERVIEW_READ,
    },
}

SYSTEM_ROLE_NAMES: dict[Role, str] = {
    Role.ADMIN: "Administración",
    Role.CLIENT: "Cliente",
    Role.VETERINARIAN: "Veterinario",
}

# Lo que el rol de sistema de administración no puede perder: sin esto nadie
# podría volver a editar roles y la clínica quedaría sin forma de corregirlo.
PROTECTED_ADMIN_PERMISSIONS: frozenset[Permission] = frozenset({Permission.ROLES_MANAGE})


def allowed_for(account_kind: Role) -> frozenset[Permission]:
    """Los permisos que un rol de ese tipo de cuenta puede tener."""
    return frozenset(
        permission for permission, info in CATALOG.items() if account_kind in info.account_kinds
    )
