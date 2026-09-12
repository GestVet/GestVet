from __future__ import annotations

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valor de relleno para que el proyecto arranque recién clonado. No es un
# secreto: el validador de abajo impide que sobreviva fuera de depuración.
INSECURE_DEFAULT_SECRET = "cambiame-solo-sirve-en-desarrollo"

# RFC 7518, sección 3.2: una clave HMAC más corta que la salida de la función
# de hash debilita la firma. Para SHA-256 eso son 32 bytes.
MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "gestvet-api"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str = "sqlite+aiosqlite:///./gestvet.db"
    cors_allowed_origins: list[str] = ["http://localhost:5173"]
    # Con qué origen arma el enlace de recuperación de contraseña que manda
    # por correo. No es lo mismo que CORS: ese protege al servidor, este es
    # simplemente dónde vive el frontend que va a atender el enlace.
    frontend_base_url: str = "http://localhost:5173"
    # Con qué origen arma la URL de un adjunto. Se reemplaza junto con el
    # adaptador de almacenamiento el día que un archivo termine en un bucket
    # en vez de en el disco del propio servidor.
    api_base_url: str = "http://localhost:8000"
    attachments_storage_dir: str = "./var/attachments"

    jwt_secret_key: str = INSECURE_DEFAULT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 3600

    @model_validator(mode="after")
    def _validate_secret(self) -> Settings:
        if len(self.jwt_secret_key.encode()) < MIN_SECRET_LENGTH:
            raise ValueError(f"JWT_SECRET_KEY necesita al menos {MIN_SECRET_LENGTH} bytes.")
        if not self.debug and self.jwt_secret_key == INSECURE_DEFAULT_SECRET:
            raise ValueError(
                "JWT_SECRET_KEY conserva el valor de desarrollo. "
                "Definí uno propio antes de desplegar con DEBUG=false."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
