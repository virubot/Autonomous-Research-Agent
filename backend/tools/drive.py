from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.utils.config import Settings


def upload_to_drive(file_path: str, settings: Settings) -> dict[str, Any]:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except Exception as exc:
        return {
            "status": "error",
            "error": f"Google Drive dependencies are unavailable: {exc}",
        }

    credential_setting = settings.drive_service_account_json or settings.google_application_credentials
    if not credential_setting:
        return {
            "status": "error",
            "error": (
                "Google Drive credentials missing. Set GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON "
                "or GOOGLE_APPLICATION_CREDENTIALS."
            ),
        }

    credentials_path = Path(credential_setting).expanduser()
    if not credentials_path.exists():
        return {
            "status": "error",
            "error": f"Drive service account file not found: {credentials_path}",
        }

    source = Path(file_path)
    if not source.exists():
        return {
            "status": "error",
            "error": f"File not found for upload: {source}",
        }

    try:
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=["https://www.googleapis.com/auth/drive"],
        )
        service = build("drive", "v3", credentials=credentials, cache_discovery=False)

        metadata: dict[str, Any] = {"name": source.name}
        if settings.drive_folder_id:
            metadata["parents"] = [settings.drive_folder_id]

        media = MediaFileUpload(str(source), resumable=False)
        created = (
            service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id,webViewLink,webContentLink",
            )
            .execute()
        )

        file_id = created["id"]
        if settings.drive_make_public:
            service.permissions().create(
                fileId=file_id,
                body={"role": "reader", "type": "anyone"},
            ).execute()
            created = (
                service.files()
                .get(fileId=file_id, fields="id,webViewLink,webContentLink")
                .execute()
            )
    except Exception as exc:
        return {
            "status": "error",
            "error": (
                f"Google Drive upload failed: {exc}. "
                "Check service-account file permissions, Drive API enablement, and folder access."
            ),
        }

    link = (
        created.get("webViewLink")
        or created.get("webContentLink")
        or f"https://drive.google.com/file/d/{file_id}/view"
    )

    return {
        "status": "success",
        "file_id": file_id,
        "file_name": source.name,
        "link": link,
    }
