"""Image storage. `local` writes under MEDIA_ROOT (development); `supabase` uses a public Storage bucket."""

import contextlib
from functools import lru_cache
from pathlib import Path
from typing import Protocol

import httpx

from app.core.config import get_settings
from app.core.errors import ServiceUnavailableError


class StorageBackend(Protocol):
    def save(self, path: str, data: bytes, content_type: str) -> str:
        """Store the bytes and return the public URL."""

    def delete(self, paths: list[str]) -> None:
        """Best-effort removal; missing files are ignored."""


class LocalStorage:
    def __init__(self, root: Path, public_base_url: str):
        self.root = root.resolve()
        self.base_url = public_base_url.rstrip("/")

    def _target(self, path: str) -> Path:
        target = (self.root / path).resolve()
        if not target.is_relative_to(self.root):
            raise ValueError("path escapes the media root")
        return target

    def save(self, path: str, data: bytes, content_type: str) -> str:
        target = self._target(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return f"{self.base_url}/{path}"

    def delete(self, paths: list[str]) -> None:
        for path in paths:
            with contextlib.suppress(FileNotFoundError):
                self._target(path).unlink()


class SupabaseStorage:
    """Uses the Storage REST API with the service-role key, which never leaves the backend."""

    def __init__(self, url: str, service_key: str, bucket: str, client: httpx.Client | None = None):
        self.url = url.rstrip("/")
        self.bucket = bucket
        self.client = client or httpx.Client(timeout=20)
        self.headers = {"Authorization": f"Bearer {service_key}", "apikey": service_key}

    def save(self, path: str, data: bytes, content_type: str) -> str:
        r = self.client.post(
            f"{self.url}/storage/v1/object/{self.bucket}/{path}",
            content=data,
            headers={**self.headers, "Content-Type": content_type, "x-upsert": "true"},
        )
        if r.status_code >= 400:
            raise ServiceUnavailableError("Image storage rejected the upload.")
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{path}"

    def delete(self, paths: list[str]) -> None:
        if not paths:
            return
        with contextlib.suppress(httpx.HTTPError):
            self.client.request(
                "DELETE",
                f"{self.url}/storage/v1/object/{self.bucket}",
                json={"prefixes": paths},
                headers=self.headers,
            )


@lru_cache
def get_storage() -> StorageBackend:
    s = get_settings()
    if s.storage_backend == "supabase":
        if not (s.supabase_url and s.supabase_service_role_key):
            raise ServiceUnavailableError("Supabase storage is not configured.")
        return SupabaseStorage(
            s.supabase_url, s.supabase_service_role_key, s.supabase_storage_bucket
        )
    return LocalStorage(Path(s.media_root), s.public_media_url)
