from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any

from backend.utils.config import Settings

try:
    import google.auth as google_auth
    from google.auth.exceptions import DefaultCredentialsError
    import vertexai
    from vertexai.generative_models import GenerationConfig, GenerativeModel
except Exception:  # pragma: no cover - runtime dependency
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
        self.fallback_model_instance = None
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
            self.model = None
            return

        if vertexai is None or GenerativeModel is None:
            self._init_error = "google-cloud-aiplatform is not installed."
            self.model = None
            return

        try:
            credentials = None
            if google_auth is not None:
                credentials, _ = google_auth.default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
            vertexai.init(
                project=self.settings.google_cloud_project,
                location=self.settings.google_cloud_location,
                credentials=credentials,
            )
            self.model = GenerativeModel(self.settings.gemini_model)
            self.fallback_model_instance = GenerativeModel(self.settings.fallback_model)
            self._init_error = None
        except DefaultCredentialsError as exc:  # pragma: no cover - env-specific
            self._init_error = (
                "Vertex AI credentials are unavailable. Configure "
                "GOOGLE_APPLICATION_CREDENTIALS with a service account JSON path or "
                "set Application Default Credentials. "
                f"Details: {exc}"
            )
            self.model = None
        except Exception as exc:  # pragma: no cover - cloud-specific
            self._init_error = f"Vertex initialization failed: {exc}"
            self.model = None

    def ensure_available(self) -> None:
        if self.model is not None:
            return
        raise VertexConfigurationError(
            self._init_error
            or "Vertex Gemini is unavailable. Check Vertex AI configuration."
        )

    def validate_startup(self) -> None:
        self.ensure_available()

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

        last_error: Exception | None = None
        for attempt in range(1, self.settings.gemini_max_retries + 1):
            try:
                response = self._generate_content_with_timeout(
                    model=self.model,
                    prompt=prompt,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                )
                text = self._extract_text(response).strip()
                if not text:
                    raise VertexGenerationError("Gemini returned an empty response.")
                return text
            except Exception as exc:
                err_str = str(exc).lower()
                last_error = exc
                logger.exception(f"Gemini call failed (attempt {attempt}): {exc}")
                
                # Check for specific fatal errors
                if "api not enabled" in err_str or "service_disabled" in err_str:
                    raise VertexConfigurationError("Vertex AI API is not enabled in your Google Cloud Project. Please enable it in the GCP Console.") from exc
                
                # Check for model not found and try fallback
                if "404" in err_str and "publisher model not found" in err_str:
                    logger.warning(f"Model {self.settings.gemini_model} not found. Attempting fallback to {self.settings.fallback_model}.")
                    try:
                        response = self._generate_content_with_timeout(
                            model=self.fallback_model_instance,
                            prompt=prompt,
                            temperature=temperature,
                            max_output_tokens=max_output_tokens,
                        )
                        text = self._extract_text(response).strip()
                        if not text:
                            raise VertexGenerationError("Gemini fallback returned an empty response.")
                        return text
                    except Exception as fallback_exc:
                        logger.exception(f"Fallback model call failed: {fallback_exc}")
                        raise VertexGenerationError(f"Both primary model ({self.settings.gemini_model}) and fallback ({self.settings.fallback_model}) failed.") from fallback_exc

                if attempt >= self.settings.gemini_max_retries:
                    break
                sleep_seconds = min(2 ** (attempt - 1), 8)
                logger.warning(
                    "Retrying in %ss due to error: %s",
                    sleep_seconds,
                    exc,
                )
                time.sleep(sleep_seconds)

        raise VertexGenerationError(
            f"Gemini generation failed after {self.settings.gemini_max_retries} attempts: {last_error}"
        )

    def generate_json(self, prompt: str) -> dict[str, Any]:
        raw = self.generate_text(
            (
                f"{prompt}\n\n"
                "Return ONLY valid JSON with double-quoted keys. Do not include markdown code fences."
            ),
            temperature=0.1,
            max_output_tokens=3072,
        )
        from backend.utils.json_utils import safe_parse_json
        result = safe_parse_json(raw, context="generate_json")
        if not isinstance(result, dict):
            raise VertexGenerationError(
                "Gemini returned invalid JSON output (not an object)."
            )
        return result

    def generate_json_strict(
        self,
        prompt: str,
        temperature: float = 0.15,
        max_output_tokens: int = 16384,
    ) -> dict[str, Any]:
        """
        Generate JSON using response_mime_type constraint when available.
        Falls back to text generation + robust parser if the API doesn't support it.
        """
        self.ensure_available()
        if not GenerationConfig or not self.model:
            raise VertexConfigurationError("Vertex Gemini dependencies unavailable.")

        # Try with response_mime_type for strict JSON enforcement
        strict_config = None
        try:
            strict_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",
            )
        except Exception:
            # Older SDK versions don't support response_mime_type
            strict_config = None

        if strict_config is not None:
            last_error: Exception | None = None
            for attempt in range(1, self.settings.gemini_max_retries + 1):
                try:
                    with ThreadPoolExecutor(max_workers=1) as pool:
                        future = pool.submit(
                            self.model.generate_content,
                            prompt,
                            generation_config=strict_config,
                        )
                        response = future.result(timeout=self.settings.gemini_timeout_seconds)
                    raw = self._extract_text(response).strip()
                    from backend.utils.json_utils import safe_parse_json
                    parsed = safe_parse_json(raw, context="generate_json_strict")
                    if isinstance(parsed, dict):
                        return parsed
                    raise VertexGenerationError("Gemini JSON response was not a dict.")
                except Exception as exc:
                    last_error = exc
                    if attempt < self.settings.gemini_max_retries:
                        sleep_sec = min(2 ** (attempt - 1), 8)
                        logger.warning("JSON strict attempt %d failed: %s — retrying in %ds", attempt, exc, sleep_sec)
                        time.sleep(sleep_sec)
            logger.warning("JSON strict mode failed after retries. Falling back to text mode.")

        # Fallback: text mode + robust parser
        full_prompt = (
            f"{prompt}\n\n"
            "CRITICAL: Return ONLY valid JSON. No markdown. No triple backticks. "
            "No comments. No trailing commas. No raw LaTeX. "
            "All backslashes must be double-escaped (e.g. \\\\alpha). "
            "JSON must be parseable with json.loads()."
        )
        raw = self.generate_text(full_prompt, temperature=temperature, max_output_tokens=max_output_tokens)
        from backend.utils.json_utils import safe_parse_json, extract_paper_sections
        parsed = safe_parse_json(raw, context="generate_json_strict_fallback")
        if isinstance(parsed, dict):
            return parsed
        # Last resort: field extraction
        recovered = extract_paper_sections(raw)
        if recovered:
            logger.warning("Recovered partial paper data via field extraction.")
            return recovered
        raise VertexGenerationError(
            "Gemini returned unparseable output even after all repair attempts."
        )

    def _generate_content_with_timeout(
        self,
        model: Any,
        prompt: str,
        temperature: float,
        max_output_tokens: int,
    ) -> Any:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                model.generate_content,  # type: ignore[union-attr]
                prompt,
                generation_config=GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
            try:
                return future.result(timeout=self.settings.gemini_timeout_seconds)
            except FuturesTimeoutError as exc:
                future.cancel()
                raise VertexGenerationError(
                    f"Gemini request timed out after {self.settings.gemini_timeout_seconds}s."
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
        from backend.utils.json_utils import strip_code_fences
        return strip_code_fences(text)