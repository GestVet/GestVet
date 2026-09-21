"""Pruebas del adaptador de almacenamiento de Supabase Storage."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from gestvet.core.attachments import (
    LocalDiskAttachmentStorage,
    SupabaseAttachmentStorage,
    create_attachment_storage,
)
from gestvet.core.config import Settings


async def test_supabase_storage_save_exitoso() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json={"Key": "attachments/clinical-entries/1/foto.png"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        storage = SupabaseAttachmentStorage(
            supabase_url="https://testproject.supabase.co",
            service_role_key="service-role-secret-token",
            bucket="attachments",
            client=client,
        )
        await storage.save(
            key="clinical-entries/1/foto.png",
            content=b"bytes-de-imagen",
            content_type="image/png",
        )

    assert captured_request is not None
    assert captured_request.method == "POST"
    assert (
        str(captured_request.url)
        == "https://testproject.supabase.co/storage/v1/object/attachments/clinical-entries/1/foto.png"
    )
    assert captured_request.headers["apikey"] == "service-role-secret-token"
    assert captured_request.headers["authorization"] == "Bearer service-role-secret-token"
    assert captured_request.headers["content-type"] == "image/png"
    assert captured_request.headers["x-upsert"] == "true"
    assert captured_request.read() == b"bytes-de-imagen"


async def test_supabase_storage_lee_con_la_clave_de_servicio() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, content=b"bytes-de-imagen")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        storage = SupabaseAttachmentStorage(
            supabase_url="https://testproject.supabase.co",
            service_role_key="service-role-secret-token",
            bucket="attachments",
            client=client,
        )
        content = await storage.read("clinical-entries/1/foto.png")

    assert content == b"bytes-de-imagen"
    assert captured_request is not None
    assert captured_request.method == "GET"
    # Nunca la ruta `/public/`: el bucket es privado.
    assert (
        str(captured_request.url)
        == "https://testproject.supabase.co/storage/v1/object/attachments/clinical-entries/1/foto.png"
    )
    assert captured_request.headers["authorization"] == "Bearer service-role-secret-token"


@pytest.mark.parametrize("status_code", [400, 404])
async def test_supabase_storage_lee_un_archivo_inexistente(status_code: int) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": "Object not found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        storage = SupabaseAttachmentStorage(
            supabase_url="https://testproject.supabase.co",
            service_role_key="service-role-secret-token",
            client=client,
        )
        with pytest.raises(FileNotFoundError):
            await storage.read("clinical-entries/1/nada.png")


async def test_disco_local_guarda_lee_y_borra(tmp_path: Path) -> None:
    storage = LocalDiskAttachmentStorage(storage_dir=str(tmp_path))

    await storage.save("clinical-entries/1/foto.png", b"bytes", "image/png")
    assert await storage.read("clinical-entries/1/foto.png") == b"bytes"

    await storage.delete("clinical-entries/1/foto.png")
    with pytest.raises(FileNotFoundError):
        await storage.read("clinical-entries/1/foto.png")


async def test_disco_local_no_sale_de_su_directorio(tmp_path: Path) -> None:
    (tmp_path / "secreto.txt").write_bytes(b"no")
    storage = LocalDiskAttachmentStorage(storage_dir=str(tmp_path / "adjuntos"))

    with pytest.raises(FileNotFoundError):
        await storage.read("../secreto.txt")


async def test_supabase_storage_save_falla_si_api_retorna_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "Internal Server Error"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        storage = SupabaseAttachmentStorage(
            supabase_url="https://testproject.supabase.co",
            service_role_key="service-role-secret-token",
            bucket="attachments",
            client=client,
        )
        with pytest.raises(httpx.HTTPStatusError):
            await storage.save(
                key="foto.png",
                content=b"bytes",
                content_type="image/png",
            )


async def test_supabase_storage_delete_exitoso() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json={"message": "Deleted"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        storage = SupabaseAttachmentStorage(
            supabase_url="https://testproject.supabase.co",
            service_role_key="service-role-secret-token",
            bucket="attachments",
            client=client,
        )
        await storage.delete("clinical-entries/1/foto.png")

    assert captured_request is not None
    assert captured_request.method == "DELETE"
    assert (
        str(captured_request.url)
        == "https://testproject.supabase.co/storage/v1/object/attachments/clinical-entries/1/foto.png"
    )
    assert captured_request.headers["apikey"] == "service-role-secret-token"
    assert captured_request.headers["authorization"] == "Bearer service-role-secret-token"


async def test_supabase_storage_delete_tolera_404() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "Object not found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        storage = SupabaseAttachmentStorage(
            supabase_url="https://testproject.supabase.co",
            service_role_key="service-role-secret-token",
            bucket="attachments",
            client=client,
        )
        # No debe lanzar excepción si el archivo ya no existía
        await storage.delete("foto.png")


def test_fabrica_create_attachment_storage() -> None:
    # Caso 1: Con Supabase configurado -> SupabaseAttachmentStorage
    settings_supabase = Settings(
        supabase_url="https://xyz.supabase.co",
        supabase_service_role_key="clave-secreta",
        supabase_storage_bucket="archivos",
    )
    storage_supabase = create_attachment_storage(settings_supabase)
    assert isinstance(storage_supabase, SupabaseAttachmentStorage)
    assert storage_supabase._supabase_url == "https://xyz.supabase.co"
    assert storage_supabase._bucket == "archivos"

    # Caso 2: Sin credenciales de Supabase -> LocalDiskAttachmentStorage
    settings_local = Settings(
        supabase_url="",
        supabase_service_role_key="",
        attachments_storage_dir="./var/custom_attachments",
    )
    storage_local = create_attachment_storage(settings_local)
    assert isinstance(storage_local, LocalDiskAttachmentStorage)
