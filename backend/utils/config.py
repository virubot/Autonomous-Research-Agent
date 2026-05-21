from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    google_cloud_project: str | None
    google_cloud_location: str
    gemini_model: str
    fallback_model: str
    google_application_credentials: str | None
    memory_db_path: Path
    tool_db_path: Path
    upload_dir: Path
    generated_dir: Path
    drive_service_account_json: str | None
    drive_folder_id: str | None
    drive_make_public: bool
    gemini_timeout_seconds: int
    gemini_max_retries: int
    strict_startup_validation: bool
    mcp_enabled: bool

    @property
    def vertex_ready(self) -> bool:
        return bool(self.google_cloud_project and self.google_cloud_location)

    @property
    def google_application_credentials_path(self) -> Path | None:
        if not self.google_application_credentials:
            return None
        return Path(self.google_application_credentials).expanduser()

    @property
    def drive_service_account_path(self) -> Path | None:
        if not self.drive_service_account_json:
            return None
        return Path(self.drive_service_account_json).expanduser()

    def validate_vertex_settings(self) -> list[str]:
        errors: list[str] = []
        if not self.google_cloud_project:
            errors.append("GOOGLE_CLOUD_PROJECT is not configured.")
        if not self.google_cloud_location:
            errors.append("GOOGLE_CLOUD_LOCATION is not configured.")

        credentials_path = self.google_application_credentials_path
        if self.google_application_credentials and credentials_path and not credentials_path.exists():
            errors.append(
                "GOOGLE_APPLICATION_CREDENTIALS points to a missing file: "
                f"{credentials_path}"
            )
        return errors

    def validate_drive_settings(self) -> list[str]:
        errors: list[str] = []
        credentials_path = self.drive_service_account_path
        if self.drive_service_account_json and credentials_path and not credentials_path.exists():
            errors.append(
                "GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON points to a missing file: "
                f"{credentials_path}"
            )
        return errors


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    upload_dir = PROJECT_ROOT / "uploads"
    generated_dir = PROJECT_ROOT / "generated_outputs"
    upload_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        google_cloud_project=os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID"),
        google_cloud_location=os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GCP_LOCATION", "us-central1"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        fallback_model=os.getenv("FALLBACK_MODEL", "gemini-2.5-flash-lite"),
        google_application_credentials=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        memory_db_path=PROJECT_ROOT / "agent_memory.db",
        tool_db_path=PROJECT_ROOT / "agent_events.db",
        upload_dir=upload_dir,
        generated_dir=generated_dir,
        drive_service_account_json=os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON"),
        drive_folder_id=os.getenv("GOOGLE_DRIVE_FOLDER_ID"),
        drive_make_public=_as_bool(os.getenv("GOOGLE_DRIVE_PUBLIC"), default=True),
        gemini_timeout_seconds=max(15, int(os.getenv("GEMINI_TIMEOUT_SECONDS", "120"))),
        gemini_max_retries=max(1, int(os.getenv("GEMINI_MAX_RETRIES", "3"))),
        strict_startup_validation=_as_bool(
            os.getenv("STRICT_STARTUP_VALIDATION"), default=True
        ),
        mcp_enabled=_as_bool(os.getenv("MCP_ENABLED"), default=True),
    )
