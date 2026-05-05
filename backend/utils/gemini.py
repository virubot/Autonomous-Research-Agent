from __future__ import annotations

import json
import logging
from typing import Any

from backend.utils.config import Settings

try:
    import google.auth as google_auth
    from google.auth.exceptions import DefaultCredentialsError
    import vertexai
    from vertexai.generative_models import GenerationConfig, GenerativeModel
except Exception:  # pragma: no cover - handled at runtime
    google_auth = None
    DefaultCredentialsError = Exception
    vertexai = None
    GenerationConfig = None
    GenerativeModel = None


logger = logging.getLogger(__name__)


class VertexConfigurationError(RuntimeError):
    pass


class VertexGenerationError(RuntimeError):
    pass


class VertexGeminiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model = None
        self._init_error: str | None = None
        self._initialize()

    @property
    def is_available(self) -> bool:
        return self.model is not None

    @property
    def init_error(self) -> str | None:
        return self._init_error

    def _initialize(self) -> None:
        settings_errors = self.settings.validate_vertex_settings()
        if settings_errors:
            self._init_error = " ".join(settings_errors)
            return

        if vertexai is None or GenerativeModel is None:
            self._init_error = "google-cloud-aiplatform is not installed."
            return

        try:
            credentials = None
            if google_auth is not None:
                credentials, _ = google_auth.default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
            vertexai.init(
                project=self.settings.gcp_project_id,
                location=self.settings.gcp_location,
                credentials=credentials,
            )
            self.model = GenerativeModel(self.settings.gemini_model)
            self._init_error = None
        except DefaultCredentialsError as exc:  # pragma: no cover - env-specific
            self._init_error = (
                "Vertex AI credentials are unavailable. Configure "
                "GOOGLE_APPLICATION_CREDENTIALS or Application Default Credentials. "
                f"Details: {exc}"
            )
            self.model = None
        except Exception as exc:  # pragma: no cover - depends on cloud env
            self._init_error = str(exc)
            self.model = None

    def ensure_available(self) -> None:
        if self.model is not None:
            return
        raise VertexConfigurationError(
            self._init_error
            or "Vertex Gemini is unavailable. Check Vertex AI configuration."
        )

    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_output_tokens: int = 2048,
    ) -> str:
        self.ensure_available()
        if not GenerationConfig or not self.model:
            raise VertexConfigurationError(
                "Vertex Gemini dependencies are unavailable. Install google-cloud-aiplatform."
            )

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
        except Exception as exc:  # pragma: no cover - depends on cloud env
            logger.exception("Gemini text generation failed")
            raise VertexGenerationError(f"Gemini generation failed: {exc}") from exc

        text = self._extract_text(response).strip()
        if not text:
            raise VertexGenerationError("Gemini returned an empty response.")
        return text

    def generate_json(self, prompt: str) -> dict[str, Any]:
        raw = self.generate_text(
            f"{prompt}\n\nReturn ONLY valid JSON. Do not include markdown code fences.",
            temperature=0.1,
            max_output_tokens=2048,
        )
        cleaned = self._strip_code_fences(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise VertexGenerationError(
                f"Gemini returned invalid JSON output: {exc}"
            ) from exc

    @staticmethod
    def _extract_text(response: Any) -> str:
        direct_text = getattr(response, "text", None)
        if direct_text:
            return str(direct_text)

        candidates = getattr(response, "candidates", None) or []
        fragments: list[str] = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            parts = getattr(content, "parts", None) or []
            for part in parts:
                text = getattr(part, "text", None)
                if text:
                    fragments.append(str(text))
        return "\n".join(fragments)

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        value = text.strip()
        if value.startswith("```"):
            lines = value.splitlines()
            if len(lines) >= 3 and lines[-1].strip() == "```":
                return "\n".join(lines[1:-1]).strip()
        return value
