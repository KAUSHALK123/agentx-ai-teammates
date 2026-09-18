import os
import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple
from app.models.input import InputErrorCode, InputType


# Max upload size: 10 MB default
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Allowed file extensions mapped to InputType and standard MIME
ALLOWED_EXTENSIONS: Dict[str, Tuple[InputType, str]] = {
    ".txt": (InputType.TEXT, "text/plain"),
    ".pdf": (InputType.PDF, "application/pdf"),
    ".csv": (InputType.CSV, "text/csv"),
    ".doc": (InputType.DOCX, "application/msword"),
    ".docx": (InputType.DOCX, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ".png": (InputType.IMAGE, "image/png"),
    ".jpg": (InputType.IMAGE, "image/jpeg"),
    ".jpeg": (InputType.IMAGE, "image/jpeg"),
    ".webp": (InputType.IMAGE, "image/webp"),
    ".mp3": (InputType.AUDIO, "audio/mpeg"),
    ".wav": (InputType.AUDIO, "audio/wav"),
    ".m4a": (InputType.AUDIO, "audio/mp4"),
    ".ogg": (InputType.AUDIO, "audio/ogg"),
}


class StorageError(Exception):
    """Exception raised by storage service operations with structured error codes."""
    def __init__(self, code: InputErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class IStorageService(ABC):
    """Abstract interface for storing and retrieving business input files."""

    @abstractmethod
    async def save_file(
        self,
        filename: str,
        content: bytes,
        mime_type: Optional[str] = None,
    ) -> Tuple[str, InputType, str, int]:
        """Save a file and return (content_reference, input_type, sanitized_filename, size_bytes)."""
        pass

    @abstractmethod
    async def get_file(self, content_reference: str) -> bytes:
        """Retrieve raw file content bytes using content reference."""
        pass

    @abstractmethod
    async def get_file_path(self, content_reference: str) -> Optional[str]:
        """Get local filesystem path for the file if available (safe, validated path)."""
        pass

    @abstractmethod
    async def delete_file(self, content_reference: str) -> bool:
        """Delete stored file."""
        pass


class LocalStorageService(IStorageService):
    """Local storage implementation storing uploaded files securely in data/uploads/."""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = Path(base_dir).resolve()
        else:
            # Default to repo root / data / uploads
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            self.base_dir = (repo_root / "data" / "uploads").resolve()

        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename against path traversal and dangerous characters."""
        # Strip path traversal components
        basename = os.path.basename(filename).strip()
        # Remove any path separators or null bytes
        clean = re.sub(r'[/\\:\0]', '_', basename)
        # Remove dangerous shell/control characters, keeping alphanumeric, dot, hyphen, underscore
        clean = re.sub(r'[^a-zA-Z0-9._-]', '_', clean)
        # Collapse multiple underscores
        clean = re.sub(r'_+', '_', clean).strip('._')
        return clean or "unnamed_input"

    def validate_file(
        self,
        filename: str,
        content: bytes,
        declared_mime: Optional[str] = None,
    ) -> Tuple[InputType, str]:
        """Validate file size, extension, and determine InputType and effective MIME."""
        # 1. Size check
        size = len(content)
        if size > MAX_FILE_SIZE_BYTES:
            raise StorageError(
                InputErrorCode.FILE_TOO_LARGE,
                f"File size {size} bytes exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES} bytes (10MB).",
            )
        if size == 0:
            raise StorageError(
                InputErrorCode.INVALID_FILE,
                "File content is empty (0 bytes).",
            )

        # 2. Extension check
        ext = os.path.splitext(filename.lower())[1]
        if ext not in ALLOWED_EXTENSIONS:
            raise StorageError(
                InputErrorCode.UNSUPPORTED_FILE_TYPE,
                f"File extension '{ext}' is not supported. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS.keys()))}.",
            )

        input_type, default_mime = ALLOWED_EXTENSIONS[ext]
        effective_mime = declared_mime or default_mime
        return input_type, effective_mime

    def _get_safe_path(self, content_reference: str) -> Path:
        """Resolve content reference and ensure it strictly resides within self.base_dir."""
        # Prevent any path traversal
        ref_basename = os.path.basename(content_reference)
        target_path = (self.base_dir / ref_basename).resolve()
        
        try:
            target_path.relative_to(self.base_dir)
        except ValueError:
            raise StorageError(
                InputErrorCode.INVALID_FILE,
                f"Access denied: illegal content reference path traversal '{content_reference}'.",
            )
        return target_path

    async def save_file(
        self,
        filename: str,
        content: bytes,
        mime_type: Optional[str] = None,
    ) -> Tuple[str, InputType, str, int]:
        """Validate, store securely under unique storage key, and return metadata."""
        input_type, effective_mime = self.validate_file(filename, content, mime_type)
        sanitized_name = self._sanitize_filename(filename)
        
        # Generate safe unique content reference
        file_id = uuid.uuid4().hex[:16]
        content_reference = f"{file_id}_{sanitized_name}"
        
        target_path = self._get_safe_path(content_reference)
        target_path.write_bytes(content)
        
        return content_reference, input_type, sanitized_name, len(content)

    async def get_file(self, content_reference: str) -> bytes:
        """Read content bytes safely."""
        target_path = self._get_safe_path(content_reference)
        if not target_path.exists() or not target_path.is_file():
            raise StorageError(
                InputErrorCode.INVALID_FILE,
                f"File not found for reference: {content_reference}",
            )
        return target_path.read_bytes()

    async def get_file_path(self, content_reference: str) -> Optional[str]:
        """Return validated path."""
        target_path = self._get_safe_path(content_reference)
        if target_path.exists() and target_path.is_file():
            return str(target_path)
        return None

    async def delete_file(self, content_reference: str) -> bool:
        """Delete stored file safely."""
        target_path = self._get_safe_path(content_reference)
        if target_path.exists() and target_path.is_file():
            target_path.unlink()
            return True
        return False


_storage_service: Optional[IStorageService] = None


def get_storage_service() -> IStorageService:
    """Return singleton instance of the configured storage service."""
    global _storage_service
    if _storage_service is None:
        _storage_service = LocalStorageService()
    return _storage_service


def set_storage_service(service: IStorageService) -> None:
    """Override storage service (primarily for testing)."""
    global _storage_service
    _storage_service = service
