import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.config.settings import get_settings
from app.models.input import InputErrorCode

logger = logging.getLogger("agentx.transcription")


class TranscriptionResult(BaseModel):
    """Structured result of an audio transcription."""
    transcript: str
    confidence: float = 1.0
    duration_seconds: Optional[float] = None
    language: str = "en"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranscriptionError(Exception):
    """Exception raised when transcription fails or is unconfigured."""
    def __init__(self, code: InputErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class BaseTranscriptionProvider(ABC):
    """Abstract interface for pluggable voice/audio transcription providers."""

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, filename: str) -> TranscriptionResult:
        """Transcribe audio bytes to text or raise TranscriptionError."""
        pass


class MockTranscriptionProvider(BaseTranscriptionProvider):
    """Deterministic mock transcription provider for testing and offline demos."""

    def __init__(self, default_text: Optional[str] = None):
        self.default_text = default_text or "Customer complaint: My payment of 5000 rupees was debited but the order ORD-5001 is still showing pending. Please help immediately."
        self.transcriptions: Dict[str, str] = {}

    def register_transcription(self, filename_or_key: str, transcript: str) -> None:
        """Register specific transcript for a given filename."""
        self.transcriptions[filename_or_key] = transcript

    async def transcribe(self, audio_bytes: bytes, filename: str) -> TranscriptionResult:
        if not audio_bytes:
            raise TranscriptionError(
                InputErrorCode.TRANSCRIPTION_FAILED,
                "Audio file contains no data.",
            )
        
        # Check custom registration
        for key, text in self.transcriptions.items():
            if key in filename:
                return TranscriptionResult(
                    transcript=text,
                    confidence=0.98,
                    duration_seconds=12.5,
                    metadata={"provider": "mock", "filename": filename},
                )

        return TranscriptionResult(
            transcript=self.default_text,
            confidence=0.95,
            duration_seconds=15.0,
            metadata={"provider": "mock", "filename": filename},
        )


class UnconfiguredTranscriptionProvider(BaseTranscriptionProvider):
    """Provider used when no transcription service or API key is configured."""

    async def transcribe(self, audio_bytes: bytes, filename: str) -> TranscriptionResult:
        raise TranscriptionError(
            InputErrorCode.TRANSCRIPTION_NOT_CONFIGURED,
            "No voice transcription service is configured. To enable audio transcription, "
            "provide a valid GEMINI_API_KEY or configure a dedicated TranscriptionProvider.",
        )


class GeminiAudioTranscriptionProvider(BaseTranscriptionProvider):
    """Transcribes audio using Google GenAI / Gemini multi-modal audio capabilities."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name

    async def transcribe(self, audio_bytes: bytes, filename: str) -> TranscriptionResult:
        if not audio_bytes:
            raise TranscriptionError(
                InputErrorCode.TRANSCRIPTION_FAILED,
                "Empty audio payload.",
            )
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Determine audio mime
            ext = filename.lower().split(".")[-1]
            mime_map = {
                "mp3": "audio/mp3",
                "wav": "audio/wav",
                "m4a": "audio/m4a",
                "ogg": "audio/ogg",
            }
            mime_type = mime_map.get(ext, "audio/mp3")

            response = client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    "Please transcribe this business audio recording verbatim. Output ONLY the exact transcription text without any commentary or explanation.",
                ],
            )
            transcript_text = (response.text or "").strip()
            if not transcript_text:
                raise TranscriptionError(
                    InputErrorCode.TRANSCRIPTION_FAILED,
                    "Transcription provider returned empty text.",
                )

            return TranscriptionResult(
                transcript=transcript_text,
                confidence=0.92,
                metadata={"provider": "gemini", "model": self.model_name},
            )
        except TranscriptionError:
            raise
        except Exception as exc:
            logger.error("Gemini transcription failed for %s: %s", filename, exc)
            raise TranscriptionError(
                InputErrorCode.TRANSCRIPTION_FAILED,
                f"Audio transcription failed: {str(exc)}",
            )


_transcription_provider: Optional[BaseTranscriptionProvider] = None


def get_transcription_provider() -> BaseTranscriptionProvider:
    """Return the active transcription provider."""
    global _transcription_provider
    if _transcription_provider is None:
        settings = get_settings()
        if settings.gemini_api_key:
            _transcription_provider = GeminiAudioTranscriptionProvider(api_key=settings.gemini_api_key)
        else:
            _transcription_provider = UnconfiguredTranscriptionProvider()
    return _transcription_provider


def set_transcription_provider(provider: Optional[BaseTranscriptionProvider]) -> None:
    """Set or override transcription provider (e.g. for testing)."""
    global _transcription_provider
    _transcription_provider = provider
